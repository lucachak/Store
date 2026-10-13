import datetime
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

import Core.billing as billing
from Checkout.tests import stripe_subscription
from Subscription.models import (
    Subscription,
    SubscriptionPrice,
    SubscriptionStatus,
    UserSubscription,
)

User = get_user_model()


class BillingHelperTests(TestCase):
    def test_minor_units_has_no_float_error(self):
        self.assertEqual(billing.to_minor_units(Decimal("19.99")), 1999)
        self.assertEqual(billing.to_minor_units(Decimal("0.29")), 29)

    def test_serialize_reads_period_from_item_or_subscription(self):
        from_item = billing.serialize_subscription(stripe_subscription())
        self.assertEqual(from_item["status"], "active")
        self.assertIsNotNone(from_item["current_period_end"])
        legacy = {"status": "active", "current_period_start": 1, "current_period_end": 2, "items": {"data": []}}
        self.assertEqual(billing.serialize_subscription(legacy)["current_period_end"].timestamp(), 2)


class PlanModelTests(TestCase):
    @override_settings(STRIPE_SECRET_KEY="")
    def test_saving_without_stripe_does_not_raise(self):
        plan = Subscription.objects.create(name="Free")
        self.assertIsNone(plan.stripe_id)

    @override_settings(STRIPE_SECRET_KEY="sk_test_x")
    def test_stripe_product_and_price_created_once(self):
        with mock.patch("Core.billing.create_product", return_value="prod_1") as product, mock.patch(
            "Core.billing.create_price", return_value="price_1"
        ) as price:
            plan = Subscription.objects.create(name="Pro")
            sub_price = SubscriptionPrice.objects.create(subscription=plan, price=Decimal("29.00"))
            plan.save()
            sub_price.save()
        product.assert_called_once()
        price.assert_called_once()
        self.assertEqual(price.call_args.kwargs["unit_amount"], 2900)
        self.assertEqual((plan.stripe_id, sub_price.stripe_id), ("prod_1", "price_1"))

    def test_only_one_featured_price_per_plan_and_interval(self):
        plan = Subscription.objects.create(name="Pro")
        first = SubscriptionPrice.objects.create(subscription=plan, featured=True)
        second = SubscriptionPrice.objects.create(subscription=plan, featured=True)
        first.refresh_from_db()
        self.assertFalse(first.featured)
        self.assertTrue(second.featured)


class EntitlementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", "ana@example.com", "pw-12345-pw")
        self.group = Group.objects.create(name="pro-members")
        self.own_group = Group.objects.create(name="beta-testers")
        self.plan = Subscription.objects.create(name="Pro")
        self.plan.groups.add(self.group)
        self.user.groups.add(self.own_group)

    def test_groups_follow_subscription_status(self):
        record = UserSubscription.objects.create(
            user=self.user, subscription=self.plan, status=SubscriptionStatus.ACTIVE
        )
        self.assertEqual(set(self.user.groups.all()), {self.group, self.own_group})

        record.status = SubscriptionStatus.CANCELED
        record.save()
        self.assertEqual(set(self.user.groups.all()), {self.own_group})

    def test_past_due_loses_access(self):
        UserSubscription.objects.create(user=self.user, subscription=self.plan, status=SubscriptionStatus.PAST_DUE)
        self.assertNotIn(self.group, self.user.groups.all())

    def test_queryset_helpers(self):
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.plan,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + datetime.timedelta(days=3),
        )
        self.assertEqual(UserSubscription.objects.by_active_trialing().count(), 1)
        self.assertEqual(UserSubscription.objects.by_days_left(3).count(), 1)
        self.assertEqual(UserSubscription.objects.by_days_left(10).count(), 0)
        self.assertEqual(UserSubscription.objects.by_user_ids([self.user.id]).count(), 1)


class PricingViewTests(TestCase):
    def setUp(self):
        self.plan = Subscription.objects.create(name="Pro", features="One\n\nTwo")
        self.price = SubscriptionPrice.objects.create(subscription=self.plan, price=Decimal("29"))

    def test_public_pricing_lists_plans(self):
        response = self.client.get(reverse("pricing"))
        self.assertContains(response, "Pro")
        self.assertContains(response, "$29")
        self.assertContains(response, "Create an account to subscribe")

    def test_unknown_interval_is_404(self):
        self.assertEqual(self.client.get("/subscription/weekly/").status_code, 404)
        self.assertEqual(self.client.get("/subscription/year/").status_code, 404)  # no yearly prices

    def test_inactive_plans_are_hidden(self):
        self.plan.active = False
        self.plan.save()
        self.assertNotContains(self.client.get(reverse("pricing")), "$29")

    def test_billing_requires_login(self):
        response = self.client.get(reverse("user_subscription"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])


@override_settings(STRIPE_SECRET_KEY="sk_test_x")
class CancelFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", "ana@example.com", "pw-12345-pw")
        self.plan = Subscription.objects.create(name="Pro", stripe_id="prod_pro")
        SubscriptionPrice.objects.create(subscription=self.plan, stripe_id="price_pro")
        self.record = UserSubscription.objects.create(
            user=self.user, subscription=self.plan, stripe_id="sub_1", status=SubscriptionStatus.ACTIVE
        )
        self.client.force_login(self.user)

    def test_cancel_schedules_end_of_period(self):
        updated = stripe_subscription(cancel=True)
        with mock.patch("Core.billing.cancel_subscription", return_value=updated) as cancel:
            response = self.client.post(reverse("user_subscription_cancel"), {"reason": "too pricey"})
        self.assertRedirects(response, reverse("user_subscription"))
        self.assertTrue(cancel.call_args.kwargs["at_period_end"])
        self.record.refresh_from_db()
        self.assertTrue(self.record.cancel_at_period_end)
        self.assertTrue(self.record.is_active_status)

    def test_cancel_failure_is_reported_not_raised(self):
        with mock.patch("Core.billing.cancel_subscription", side_effect=billing.StripeError("boom")):
            response = self.client.post(reverse("user_subscription_cancel"), follow=True)
        self.assertContains(response, "couldn&#x27;t cancel")

    def test_resume(self):
        self.record.cancel_at_period_end = True
        self.record.save()
        with mock.patch("Core.billing.resume_subscription", return_value=stripe_subscription()):
            self.client.post(reverse("user_subscription_resume"))
        self.record.refresh_from_db()
        self.assertFalse(self.record.cancel_at_period_end)
