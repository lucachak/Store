import logging

from allauth.account.signals import email_confirmed, user_signed_up
from django.conf import settings
from django.db import models
from django.dispatch import receiver

import Core.billing as billing

logger = logging.getLogger(__name__)


class Customer(models.Model):
    """Links a user to their Stripe customer.

    The Stripe customer is created lazily, once the email is confirmed or when
    the user first starts a checkout, never inside `save()`.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(blank=True, null=True)
    init_email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email or self.user.get_username()

    def ensure_stripe_customer(self) -> str:
        """Return the Stripe customer id, creating the customer if needed."""
        if not self.stripe_id:
            self.stripe_id = billing.create_customer(
                email=self.user.email or self.init_email or "",
                name=self.user.get_full_name(),
                metadata={"user_id": self.user_id},
            )
            self.save(update_fields=["stripe_id"])
        return self.stripe_id


@receiver(user_signed_up)
def create_customer_on_signup(request, user, **kwargs):
    Customer.objects.get_or_create(
        user=user, defaults={"init_email": user.email, "init_email_confirmed": False}
    )


@receiver(email_confirmed)
def create_stripe_customer_on_confirm(request, email_address, **kwargs):
    customer, _ = Customer.objects.get_or_create(
        user=email_address.user, defaults={"init_email": email_address.email}
    )
    if not customer.init_email_confirmed:
        customer.init_email_confirmed = True
        customer.save(update_fields=["init_email_confirmed"])
    if billing.is_configured():
        try:
            customer.ensure_stripe_customer()
        except billing.StripeError:
            # Not fatal: the customer is created again at checkout.
            logger.exception("Could not create a Stripe customer for user %s", customer.user_id)
