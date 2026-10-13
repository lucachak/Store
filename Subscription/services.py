"""
Keeps `UserSubscription` in step with Stripe.

Checkout success pages and webhooks both end up here, so a subscription is
written the same way no matter which one arrives first and handling an event
twice is harmless.
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction

import Core.billing as billing
from Customers.models import Customer

from .models import (
    ENTITLED_STATUSES,
    Subscription,
    SubscriptionPrice,
    UserSubscription,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def user_for_stripe_customer(customer_id: str):
    customer = Customer.objects.select_related("user").filter(stripe_id=customer_id).first()
    return customer.user if customer else None


def plan_for_stripe_price(price_id: str | None):
    if not price_id:
        return None
    return Subscription.objects.filter(subscriptionprice__stripe_id=price_id).first()


@transaction.atomic
def sync_user_subscription(user, stripe_subscription) -> UserSubscription | None:
    """Write a Stripe subscription onto the user's local record.

    A user has one local subscription. When an event is about a subscription
    that is not the current one it only replaces the current one if it is
    itself entitled, which is what happens when someone changes plan. Late
    events about an old, already replaced subscription are ignored.
    """
    incoming_id = stripe_subscription.get("id")
    data = billing.serialize_subscription(stripe_subscription)
    plan = plan_for_stripe_price(billing.subscription_price_id(stripe_subscription))

    record, _created = UserSubscription.objects.select_for_update().get_or_create(user=user)
    previous_id = record.stripe_id

    if previous_id and previous_id != incoming_id:
        if data["status"] not in ENTITLED_STATUSES:
            logger.info("Ignoring %s: user %s already has %s", incoming_id, user.pk, previous_id)
            return record

    record.stripe_id = incoming_id
    record.subscription = plan or record.subscription
    record.user_cancelled = data["cancel_at_period_end"]
    for field, value in data.items():
        setattr(record, field, value)
    record.save()

    if previous_id and previous_id != incoming_id:
        _cancel_replaced_subscription(previous_id)
    return record


def _cancel_replaced_subscription(stripe_id: str) -> None:
    try:
        billing.cancel_subscription(stripe_id, reason="Replaced by a new plan")
    except billing.StripeError:
        # It may already be cancelled. A later sync_billing run cleans up.
        logger.warning("Could not cancel replaced subscription %s", stripe_id, exc_info=True)


def refresh_user_subscription(record: UserSubscription) -> bool:
    """Pull the latest state of one local subscription from Stripe."""
    if not record.stripe_id:
        return True
    try:
        stripe_subscription = billing.get_subscription(record.stripe_id)
    except (billing.StripeError, billing.BillingNotConfigured):
        logger.warning("Could not refresh subscription %s", record.stripe_id, exc_info=True)
        return False
    sync_user_subscription(record.user, stripe_subscription)
    return True


def refresh_active_subscriptions(user_ids=None, active_only=True) -> tuple[int, int]:
    """Refresh many subscriptions. Returns (refreshed, total)."""
    queryset = UserSubscription.objects.select_related("user").by_user_ids(user_ids)
    if active_only:
        queryset = queryset.by_active_trialing()
    refreshed = total = 0
    for record in queryset:
        total += 1
        refreshed += refresh_user_subscription(record)
    return refreshed, total


def cancel_dangling_subscriptions() -> int:
    """Cancel active Stripe subscriptions that no local record knows about."""
    cancelled = 0
    for customer in Customer.objects.exclude(stripe_id__isnull=True).exclude(stripe_id=""):
        for stripe_subscription in billing.list_active_subscriptions(customer.stripe_id).auto_paging_iter():
            known = UserSubscription.objects.filter(stripe_id=stripe_subscription.id).exists()
            if not known:
                billing.cancel_subscription(stripe_subscription.id, reason="Dangling subscription")
                cancelled += 1
    return cancelled


def sync_group_permissions() -> None:
    """Copy each active plan's permissions onto the plan's groups."""
    for plan in Subscription.objects.filter(active=True).prefetch_related("groups", "permissions"):
        permissions = list(plan.permissions.all())
        for group in plan.groups.all():
            group.permissions.set(permissions)
