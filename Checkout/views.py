import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import Core.billing as billing
from Customers.models import Customer
from Subscription import services
from Subscription.models import SubscriptionPrice

logger = logging.getLogger(__name__)


class CheckoutStartView(LoginRequiredMixin, View):
    """Create a Stripe Checkout session for a price and send the user there."""

    http_method_names = ["post"]

    def post(self, request, price_id, *args, **kwargs):
        price = get_object_or_404(
            SubscriptionPrice.objects.select_related("subscription"),
            pk=price_id,
            subscription__active=True,
        )
        if not billing.is_configured() or not price.stripe_id:
            messages.error(request, _("Payments are not available right now. Please try again later."))
            return redirect("pricing")

        customer, _created = Customer.objects.get_or_create(
            user=request.user, defaults={"init_email": request.user.email}
        )
        try:
            customer_id = customer.ensure_stripe_customer()
            session = billing.start_checkout_session(
                customer_id=customer_id,
                price_stripe_id=price.stripe_id,
                success_url=f"{settings.BASE_URL}{reverse('stripe-checkout-end')}",
                cancel_url=f"{settings.BASE_URL}{reverse('pricing')}",
                client_reference_id=str(request.user.pk),
            )
        except billing.StripeError:
            logger.exception("Could not start checkout for user %s", request.user.pk)
            messages.error(request, _("We couldn't start the checkout. Please try again."))
            return redirect("pricing")
        return redirect(session.url)


class CheckoutFinalizeView(LoginRequiredMixin, View):
    """Where Stripe sends the user back after paying."""

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("session_id", "")
        customer = Customer.objects.filter(user=request.user).first()
        if not session_id or not customer or not customer.stripe_id:
            return redirect("pricing")

        try:
            session = billing.get_checkout_session(session_id)
            # The session must belong to this user, or anyone could claim
            # a plan by pasting somebody else's session id.
            if session.customer != customer.stripe_id or not session.subscription:
                raise PermissionError
            stripe_subscription = billing.get_subscription(session.subscription)
        except PermissionError:
            return HttpResponseBadRequest(_("This checkout session doesn't belong to your account."))
        except (billing.StripeError, billing.BillingNotConfigured):
            logger.exception("Could not finalize checkout %s", session_id)
            messages.error(
                request,
                _("We couldn't confirm your payment yet. If you were charged, your plan will appear shortly."),
            )
            return redirect("user_subscription")

        record = services.sync_user_subscription(request.user, stripe_subscription)
        messages.success(request, _("You're subscribed. Thank you!"))
        return redirect(record.get_absolute_url())


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """Receives Stripe events. Authenticated by signature, not by session."""

    http_method_names = ["post"]
    SUBSCRIPTION_EVENTS = {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }

    def post(self, request, *args, **kwargs):
        if not settings.STRIPE_WEBHOOK_SECRET:
            return HttpResponse(status=503)
        try:
            event = billing.construct_event(
                request.body, request.META.get("HTTP_STRIPE_SIGNATURE", "")
            )
        except (ValueError, billing.SignatureVerificationError):
            return HttpResponseBadRequest()

        event_type = event["type"]
        obj = event["data"]["object"]
        try:
            if event_type == "checkout.session.completed":
                self._checkout_completed(obj)
            elif event_type in self.SUBSCRIPTION_EVENTS:
                self._subscription_changed(obj)
        except billing.StripeError:
            # A 5xx makes Stripe retry later with the same event.
            logger.exception("Stripe error handling %s", event["id"])
            return HttpResponse(status=500)
        return HttpResponse(status=200)

    @staticmethod
    def _checkout_completed(session):
        if session.get("mode") != "subscription" or not session.get("subscription"):
            return
        user = services.user_for_stripe_customer(session.get("customer"))
        if user is None:
            logger.warning("Checkout %s for unknown customer", session.get("id"))
            return
        services.sync_user_subscription(user, billing.get_subscription(session["subscription"]))

    @staticmethod
    def _subscription_changed(subscription):
        user = services.user_for_stripe_customer(subscription.get("customer"))
        if user is None:
            logger.warning("Subscription %s for unknown customer", subscription.get("id"))
            return
        services.sync_user_subscription(user, subscription)
