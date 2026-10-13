import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

import Core.billing as billing
from Customers.models import Customer
from Subscription.models import (
    Subscription,
    SubscriptionPrice,
    SubscriptionStatus,
    UserSubscription,
)

User = get_user_model()


def stripe_subscription(sub_id="sub_1", customer="cus_1", price="price_pro", status="active", cancel=False):
    return {
        "id": sub_id,
        "customer": customer,
        "status": status,
        "cancel_at_period_end": cancel,
        "items": {
            "data": [
                {
                    "price": {"id": price},
                    "current_period_start": 1_700_000_000,
                    "current_period_end": 1_702_600_000,
                }
            ]
        },
    }


class BillingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("ana", "ana@example.com", "pw-12345-pw")
        cls.customer = Customer.objects.create(user=cls.user, stripe_id="cus_1", init_email="ana@example.com")
        cls.plan = Subscription.objects.create(name="Pro", stripe_id="prod_pro")
        cls.price = SubscriptionPrice.objects.create(
            subscription=cls.plan, price="29.00", stripe_id="price_pro"
        )


@override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_x")
class WebhookTests(BillingTestCase):
    url = "/checkout/webhook/"

    def post(self, event_type, obj):
        event = {"id": "evt_1", "type": event_type, "data": {"object": obj}}
        with mock.patch("Core.billing.construct_event", return_value=event):
            return self.client.post(
                self.url, data=json.dumps(event), content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=x",
            )

    def test_rejects_bad_signature(self):
        with mock.patch(
            "Core.billing.construct_event",
            side_effect=billing.SignatureVerificationError("bad", "sig"),
        ):
            response = self.client.post(self.url, data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserSubscription.objects.exists())

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_unconfigured_secret_is_503(self):
        self.assertEqual(self.client.post(self.url, data="{}", content_type="application/json").status_code, 503)

    def test_subscription_created_grants_plan(self):
        response = self.post("customer.subscription.created", stripe_subscription())
        self.assertEqual(response.status_code, 200)
        record = UserSubscription.objects.get(user=self.user)
        self.assertEqual(record.subscription, self.plan)
        self.assertEqual(record.status, SubscriptionStatus.ACTIVE)
        self.assertEqual(record.stripe_id, "sub_1")
        self.assertIsNotNone(record.current_period_end)

    def test_events_are_idempotent(self):
        for _ in range(3):
            self.post("customer.subscription.updated", stripe_subscription())
        self.assertEqual(UserSubscription.objects.filter(user=self.user).count(), 1)

    def test_deleted_marks_canceled(self):
        self.post("customer.subscription.created", stripe_subscription())
        self.post("customer.subscription.deleted", stripe_subscription(status="canceled"))
        record = UserSubscription.objects.get(user=self.user)
        self.assertEqual(record.status, SubscriptionStatus.CANCELED)
        self.assertFalse(record.is_active_status)

    def test_scheduled_cancellation_is_mirrored(self):
        self.post("customer.subscription.updated", stripe_subscription(cancel=True))
        record = UserSubscription.objects.get(user=self.user)
        self.assertTrue(record.cancel_at_period_end)
        self.assertTrue(record.user_cancelled)

    def test_unknown_customer_is_acknowledged(self):
        response = self.post("customer.subscription.updated", stripe_subscription(customer="cus_other"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserSubscription.objects.exists())

    def test_late_event_for_replaced_subscription_is_ignored(self):
        self.post("customer.subscription.created", stripe_subscription(sub_id="sub_new"))
        with mock.patch("Core.billing.cancel_subscription"):
            self.post("customer.subscription.deleted", stripe_subscription(sub_id="sub_old", status="canceled"))
        record = UserSubscription.objects.get(user=self.user)
        self.assertEqual(record.stripe_id, "sub_new")
        self.assertTrue(record.is_active_status)

    def test_new_active_subscription_replaces_and_cancels_old(self):
        self.post("customer.subscription.created", stripe_subscription(sub_id="sub_old"))
        with mock.patch("Core.billing.cancel_subscription") as cancel:
            self.post("customer.subscription.created", stripe_subscription(sub_id="sub_new"))
        cancel.assert_called_once()
        self.assertEqual(cancel.call_args.args[0], "sub_old")
        self.assertEqual(UserSubscription.objects.get(user=self.user).stripe_id, "sub_new")

    def test_checkout_completed_syncs_subscription(self):
        session = {"id": "cs_1", "mode": "subscription", "customer": "cus_1", "subscription": "sub_1"}
        with mock.patch("Core.billing.get_subscription", return_value=stripe_subscription()):
            self.post("checkout.session.completed", session)
        self.assertEqual(UserSubscription.objects.get(user=self.user).subscription, self.plan)


@override_settings(STRIPE_SECRET_KEY="sk_test_x")
class CheckoutTests(BillingTestCase):
    def test_start_requires_login_and_post(self):
        url = reverse("sub-price-checkout", args=[self.price.pk])
        self.assertEqual(self.client.post(url).status_code, 302)  # to login
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_start_redirects_to_stripe(self):
        self.client.force_login(self.user)
        session = mock.Mock(url="https://checkout.stripe.com/c/pay/cs_1")
        with mock.patch("Core.billing.start_checkout_session", return_value=session) as start:
            response = self.client.post(reverse("sub-price-checkout", args=[self.price.pk]))
        self.assertRedirects(response, session.url, fetch_redirect_response=False)
        self.assertEqual(start.call_args.kwargs["customer_id"], "cus_1")
        self.assertEqual(start.call_args.kwargs["price_stripe_id"], "price_pro")

    def test_inactive_plan_cannot_be_bought(self):
        self.plan.active = False
        self.plan.save()
        self.client.force_login(self.user)
        response = self.client.post(reverse("sub-price-checkout", args=[self.price.pk]))
        self.assertEqual(response.status_code, 404)

    def test_success_rejects_someone_elses_session(self):
        self.client.force_login(self.user)
        session = mock.Mock(customer="cus_SOMEONE_ELSE", subscription="sub_9")
        with mock.patch("Core.billing.get_checkout_session", return_value=session):
            response = self.client.get(reverse("stripe-checkout-end"), {"session_id": "cs_1"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserSubscription.objects.exists())

    def test_success_syncs_own_session(self):
        self.client.force_login(self.user)
        session = mock.Mock(customer="cus_1", subscription="sub_1")
        with mock.patch("Core.billing.get_checkout_session", return_value=session), mock.patch(
            "Core.billing.get_subscription", return_value=stripe_subscription()
        ):
            response = self.client.get(reverse("stripe-checkout-end"), {"session_id": "cs_1"})
        self.assertRedirects(response, reverse("user_subscription"))
        self.assertEqual(UserSubscription.objects.get(user=self.user).subscription, self.plan)

    def test_success_requires_login(self):
        response = self.client.get(reverse("stripe-checkout-end"), {"session_id": "cs_1"})
        self.assertEqual(response.status_code, 302)
