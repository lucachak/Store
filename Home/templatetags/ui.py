from decimal import Decimal

from django import template
from django.conf import settings
from django.utils import formats

register = template.Library()

CURRENCY_SYMBOLS = {"usd": "$", "eur": "€", "gbp": "£", "brl": "R$", "cad": "CA$", "aud": "A$"}

STATUS_TONES = {
    "active": "ok",
    "trialing": "ok",
    "past_due": "danger",
    "unpaid": "danger",
    "canceled": "",
    "incomplete": "warn",
    "incomplete_expired": "",
    "paused": "warn",
}


@register.filter
def money(value, currency=None):
    """19 -> $19, 19.5 -> $19.50, using the active language's separators."""
    if value is None:
        return ""
    amount = Decimal(value)
    code = (currency or settings.BILLING_CURRENCY).lower()
    digits = 0 if amount == amount.to_integral_value() else 2
    number = formats.number_format(amount, decimal_pos=digits, use_l10n=True)
    symbol = CURRENCY_SYMBOLS.get(code)
    return f"{symbol}{number}" if symbol else f"{number} {code.upper()}"


@register.filter
def status_tone(status):
    return STATUS_TONES.get(status or "", "")


@register.filter
def startswith(value, prefix):
    return str(value).startswith(str(prefix))


@register.filter
def initials(user):
    name = user.get_full_name().strip() or user.email or user.get_username()
    parts = name.replace("@", " ").replace(".", " ").split()
    return "".join(part[0] for part in parts[:2]).upper() or "?"
