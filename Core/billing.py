"""
Thin wrapper around the Stripe API.

Everything that talks to Stripe goes through this module so the rest of the
project never imports `stripe` directly and can be tested by patching one place.
"""
import datetime
import logging
from decimal import Decimal

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

StripeError = stripe.StripeError
SignatureVerificationError = stripe.SignatureVerificationError


class BillingNotConfigured(RuntimeError):
    """Raised when a Stripe call is attempted without `STRIPE_SECRET_KEY`."""


def is_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def _api_key() -> str:
    if not is_configured():
        raise BillingNotConfigured("STRIPE_SECRET_KEY is not set.")
    return settings.STRIPE_SECRET_KEY


def _opts() -> dict:
    # Passing the key per call keeps this module free of global state.
    return {"api_key": _api_key()}


def to_datetime(timestamp) -> datetime.datetime | None:
    if timestamp is None:
        return None
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def to_minor_units(amount: Decimal) -> int:
    """Convert 19.99 to 1999 without float rounding errors."""
    return int((Decimal(amount) * 100).quantize(Decimal("1")))


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def subscription_price_id(subscription) -> str | None:
    items = (subscription.get("items") or {}).get("data") or []
    if not items:
        return None
    price = items[0].get("price") or {}
    return price.get("id")


def serialize_subscription(subscription) -> dict:
    """The fields we mirror locally for a Stripe subscription.

    Recent Stripe API versions moved the billing period from the subscription
    to its items, older ones keep it on the subscription. Support both.
    """
    items = (subscription.get("items") or {}).get("data") or []
    first_item = items[0] if items else {}

    def period(key):
        return first_item.get(key) or subscription.get(key)

    return {
        "status": subscription.get("status"),
        "current_period_start": to_datetime(period("current_period_start")),
        "current_period_end": to_datetime(period("current_period_end")),
        "cancel_at_period_end": bool(subscription.get("cancel_at_period_end")),
    }


# --------------------------------------------------------------------------- #
# Catalogue
# --------------------------------------------------------------------------- #
def create_customer(email: str, name: str = "", metadata: dict | None = None) -> str:
    customer = stripe.Customer.create(
        email=email, name=name or None, metadata=metadata or {}, **_opts()
    )
    return customer.id


def create_product(name: str, metadata: dict | None = None) -> str:
    product = stripe.Product.create(name=name, metadata=metadata or {}, **_opts())
    return product.id


def create_price(
    product_id: str,
    unit_amount: int,
    currency: str,
    interval: str = "month",
    metadata: dict | None = None,
) -> str:
    price = stripe.Price.create(
        product=product_id,
        unit_amount=unit_amount,
        currency=currency,
        recurring={"interval": interval},
        metadata=metadata or {},
        **_opts(),
    )
    return price.id


# --------------------------------------------------------------------------- #
# Checkout and subscriptions
# --------------------------------------------------------------------------- #
def start_checkout_session(
    customer_id: str,
    price_stripe_id: str,
    success_url: str,
    cancel_url: str,
    client_reference_id: str = "",
):
    if "{CHECKOUT_SESSION_ID}" not in success_url:
        separator = "&" if "?" in success_url else "?"
        success_url = f"{success_url}{separator}session_id={{CHECKOUT_SESSION_ID}}"
    return stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        client_reference_id=client_reference_id or None,
        line_items=[{"price": price_stripe_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        **_opts(),
    )


def get_checkout_session(session_id: str):
    return stripe.checkout.Session.retrieve(session_id, **_opts())


def get_subscription(subscription_id: str):
    return stripe.Subscription.retrieve(subscription_id, **_opts())


def list_active_subscriptions(customer_id: str):
    return stripe.Subscription.list(customer=customer_id, status="active", **_opts())


def cancel_subscription(
    subscription_id: str,
    reason: str = "",
    feedback: str = "other",
    at_period_end: bool = False,
):
    details = {"comment": reason, "feedback": feedback}
    if at_period_end:
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
            cancellation_details=details,
            **_opts(),
        )
    return stripe.Subscription.cancel(
        subscription_id, cancellation_details=details, **_opts()
    )


def resume_subscription(subscription_id: str):
    """Undo a scheduled cancellation, as long as the period hasn't ended."""
    return stripe.Subscription.modify(
        subscription_id, cancel_at_period_end=False, **_opts()
    )


def create_portal_session(customer_id: str, return_url: str):
    return stripe.billing_portal.Session.create(
        customer=customer_id, return_url=return_url, **_opts()
    )


# --------------------------------------------------------------------------- #
# Webhooks
# --------------------------------------------------------------------------- #
def construct_event(payload: bytes, signature_header: str):
    """Verify the signature and parse a webhook payload.

    Raises `ValueError` for a bad payload and `SignatureVerificationError`
    for a bad or missing signature.
    """
    return stripe.Webhook.construct_event(
        payload, signature_header, settings.STRIPE_WEBHOOK_SECRET
    )
