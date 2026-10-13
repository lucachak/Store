import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import Core.billing as billing

# When True, users keep any groups that don't belong to a plan. When False,
# a user's groups are replaced by the groups of their plan.
ALLOW_CUSTOM_GROUPS = True

SUBSCRIPTION_PERMISSIONS = [
    ("advanced", "Advanced Perm"),
    ("pro", "Pro Perm"),
    ("basic", "Basic Perm"),
    ("basic_ai", "Basic AI permission"),
]


class Subscription(models.Model):
    """A plan the customer can buy. Mirrors a Stripe product."""

    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        limit_choices_to={
            "content_type__app_label": "Subscription",
            "codename__in": [code for code, _label in SUBSCRIPTION_PERMISSIONS],
        },
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    order = models.IntegerField(default=-1, help_text="Position on the pricing page.")
    featured = models.BooleanField(default=True, help_text="Show on the pricing page.")
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    features = models.TextField(
        blank=True, null=True, help_text="One feature per line, shown on the pricing page."
    )

    class Meta:
        ordering = ["order", "featured", "-updated"]
        permissions = SUBSCRIPTION_PERMISSIONS

    def __str__(self):
        return self.name

    def get_features_as_list(self):
        if not self.features:
            return []
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.stripe_id and billing.is_configured():
            self.stripe_id = billing.create_product(
                name=self.name, metadata={"subscription_plan_id": self.pk}
            )
            super().save(update_fields=["stripe_id"])


class SubscriptionPrice(models.Model):
    """A price for a plan. Mirrors a Stripe price, which is immutable."""

    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", _("Monthly")
        YEARLY = "year", _("Yearly")

    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(
        max_length=120, default=IntervalChoices.MONTHLY, choices=IntervalChoices.choices
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("99.99"))
    order = models.IntegerField(default=-1, help_text="Position on the pricing page.")
    featured = models.BooleanField(default=True, help_text="Show on the pricing page.")
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["subscription__order", "order", "featured", "-updated"]

    def __str__(self):
        return f"{self.display_sub_name} · {self.get_interval_display()}"

    @property
    def display_features_list(self):
        return self.subscription.get_features_as_list() if self.subscription else []

    @property
    def display_sub_name(self):
        return self.subscription.name if self.subscription else _("Plan")

    @property
    def display_sub_subtitle(self):
        return self.subscription.subtitle if self.subscription else ""

    @property
    def stripe_currency(self):
        return settings.BILLING_CURRENCY

    @property
    def stripe_price(self):
        return billing.to_minor_units(self.price)

    @property
    def product_stripe_id(self):
        return self.subscription.stripe_id if self.subscription else None

    def get_checkout_url(self):
        return reverse("sub-price-checkout", kwargs={"price_id": self.pk})

    def save(self, *args, **kwargs):
        if not self.stripe_id and self.product_stripe_id and billing.is_configured():
            self.stripe_id = billing.create_price(
                product_id=self.product_stripe_id,
                unit_amount=self.stripe_price,
                currency=self.stripe_currency,
                interval=self.interval,
                metadata={"subscription_plan_price_id": self.pk},
            )
        super().save(*args, **kwargs)
        if self.featured and self.subscription:
            SubscriptionPrice.objects.filter(
                subscription=self.subscription, interval=self.interval
            ).exclude(pk=self.pk).update(featured=False)


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    TRIALING = "trialing", _("Trialing")
    INCOMPLETE = "incomplete", _("Incomplete")
    INCOMPLETE_EXPIRED = "incomplete_expired", _("Incomplete expired")
    PAST_DUE = "past_due", _("Past due")
    CANCELED = "canceled", _("Canceled")
    UNPAID = "unpaid", _("Unpaid")
    PAUSED = "paused", _("Paused")


# Statuses that give the user the plan's permissions.
ENTITLED_STATUSES = (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)


class UserSubscriptionQuerySet(models.QuerySet):
    @staticmethod
    def _day_bounds(day: datetime.datetime):
        return (
            day.replace(hour=0, minute=0, second=0, microsecond=0),
            day.replace(hour=23, minute=59, second=59, microsecond=999999),
        )

    def by_range(self, days_start=7, days_end=120):
        now = timezone.now()
        start, _unused = self._day_bounds(now + datetime.timedelta(days=days_start))
        _unused, end = self._day_bounds(now + datetime.timedelta(days=days_end))
        return self.filter(current_period_end__gte=start, current_period_end__lte=end)

    def by_days_left(self, days_left=7):
        start, end = self._day_bounds(timezone.now() + datetime.timedelta(days=days_left))
        return self.filter(current_period_end__gte=start, current_period_end__lte=end)

    def by_days_ago(self, days_ago=3):
        start, end = self._day_bounds(timezone.now() - datetime.timedelta(days=days_ago))
        return self.filter(current_period_end__gte=start, current_period_end__lte=end)

    def by_active_trialing(self):
        return self.filter(Q(status=SubscriptionStatus.ACTIVE) | Q(status=SubscriptionStatus.TRIALING))

    def by_user_ids(self, user_ids=None):
        if user_ids is None:
            return self
        if isinstance(user_ids, (int, str)):
            user_ids = [user_ids]
        return self.filter(user_id__in=list(user_ids))


class UserSubscription(models.Model):
    """The plan a user is on. Kept in sync with Stripe by `Subscription.services`."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, null=True, blank=True
    )

    objects = UserSubscriptionQuerySet.as_manager()

    def __str__(self):
        return f"{self.user} · {self.plan_name or '-'}"

    def get_absolute_url(self):
        return reverse("user_subscription")

    def get_cancel_url(self):
        return reverse("user_subscription_cancel")

    @property
    def is_active_status(self):
        return self.status in ENTITLED_STATUSES

    @property
    def plan_name(self):
        return self.subscription.name if self.subscription else None

    def serialize(self):
        return {
            "plan_name": self.plan_name,
            "status": self.status,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
        }

    def save(self, *args, **kwargs):
        if self.original_period_start is None and self.current_period_start is not None:
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)


def apply_plan_groups(sender, instance, **kwargs):
    """Give the user the groups of their plan, but only while it is paid for."""
    user = instance.user
    plan = instance.subscription if instance.is_active_status else None
    plan_group_ids = set(plan.groups.values_list("id", flat=True)) if plan else set()

    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(plan_group_ids)
        return

    # Keep the user's own groups, drop the groups of any plan they don't have now.
    all_plan_group_ids = set(
        Group.objects.filter(subscription__active=True).values_list("id", flat=True)
    )
    current = set(user.groups.values_list("id", flat=True))
    user.groups.set((current - all_plan_group_ids) | plan_group_ids)


post_save.connect(apply_plan_groups, sender=UserSubscription)
