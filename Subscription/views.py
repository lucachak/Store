import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

import Core.billing as billing
from Customers.models import Customer

from . import services
from .models import SubscriptionPrice, UserSubscription

logger = logging.getLogger(__name__)


class SubscriptionView(View):
    """Public pricing page."""

    def get(self, request, interval=SubscriptionPrice.IntervalChoices.MONTHLY, *args, **kwargs):
        intervals = SubscriptionPrice.IntervalChoices
        if interval not in intervals.values:
            raise Http404

        base = SubscriptionPrice.objects.filter(
            featured=True, subscription__active=True
        ).select_related("subscription")
        has_yearly = base.filter(interval=intervals.YEARLY).exists()
        if interval == intervals.YEARLY and not has_yearly:
            raise Http404

        current_plan_id = None
        if request.user.is_authenticated:
            current = (
                UserSubscription.objects.filter(user=request.user).select_related("subscription").first()
            )
            if current and current.is_active_status:
                current_plan_id = current.subscription_id

        context = {
            "obj_list": base.filter(interval=interval),
            "act": interval,
            "has_yearly": has_yearly,
            "mo_url": reverse("subscription_inter", kwargs={"interval": intervals.MONTHLY}),
            "yr_url": reverse("subscription_inter", kwargs={"interval": intervals.YEARLY}),
            "current_plan_id": current_plan_id,
        }
        return render(request, "Subscription/pricing.html", context)


class UserSubscriptionView(LoginRequiredMixin, View):
    """The signed-in user's plan and billing details."""

    def get(self, request, *args, **kwargs):
        record, _created = UserSubscription.objects.get_or_create(user=request.user)
        return render(request, "Subscription/user-details-view.html", {"subscription": record})

    def post(self, request, *args, **kwargs):
        """Refresh the plan details from Stripe."""
        record, _created = UserSubscription.objects.get_or_create(user=request.user)
        if services.refresh_user_subscription(record):
            messages.success(request, _("Your plan details are up to date."))
        else:
            messages.error(request, _("We couldn't refresh your plan details. Please try again."))
        return redirect(record.get_absolute_url())


class UserSubscriptionCancelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        record, _created = UserSubscription.objects.get_or_create(user=request.user)
        if not (record.stripe_id and record.is_active_status) or record.cancel_at_period_end:
            return redirect(record.get_absolute_url())
        return render(request, "Subscription/user-cancel-view.html", {"subscription": record})

    def post(self, request, *args, **kwargs):
        record, _created = UserSubscription.objects.get_or_create(user=request.user)
        if record.stripe_id and record.is_active_status:
            try:
                stripe_subscription = billing.cancel_subscription(
                    record.stripe_id,
                    reason=request.POST.get("reason", "")[:500],
                    at_period_end=True,
                )
            except (billing.StripeError, billing.BillingNotConfigured):
                logger.exception("Could not cancel subscription %s", record.stripe_id)
                messages.error(request, _("We couldn't cancel your plan. Please try again."))
                return redirect(record.get_cancel_url())
            services.sync_user_subscription(request.user, stripe_subscription)
            messages.success(request, _("Your plan will end on the last day of the billing period."))
        return redirect(record.get_absolute_url())


class UserSubscriptionResumeView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        record, _created = UserSubscription.objects.get_or_create(user=request.user)
        if record.stripe_id and record.cancel_at_period_end and record.is_active_status:
            try:
                stripe_subscription = billing.resume_subscription(record.stripe_id)
            except (billing.StripeError, billing.BillingNotConfigured):
                logger.exception("Could not resume subscription %s", record.stripe_id)
                messages.error(request, _("We couldn't resume your plan. Please try again."))
            else:
                services.sync_user_subscription(request.user, stripe_subscription)
                messages.success(request, _("Your plan will renew as usual."))
        return redirect(record.get_absolute_url())


class BillingPortalView(LoginRequiredMixin, View):
    """Send the user to Stripe's portal to manage payment methods and invoices."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        customer = Customer.objects.filter(user=request.user).first()
        if customer and customer.stripe_id:
            try:
                session = billing.create_portal_session(
                    customer.stripe_id,
                    return_url=f"{settings.BASE_URL}{reverse('user_subscription')}",
                )
                return redirect(session.url)
            except (billing.StripeError, billing.BillingNotConfigured):
                logger.exception("Could not open the billing portal for user %s", request.user.pk)
        messages.error(request, _("We couldn't open the billing portal. Please try again."))
        return redirect("user_subscription")
