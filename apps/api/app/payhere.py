"""PayHere's hash math, kept apart from the rest of the checkout so it can be tested on its own.

Two different hashes are involved, both `strtoupper(md5(...))` of a concatenation, but of different
fields: one signs the checkout form the shopper is sent to, the other verifies PayHere's payment
notification (https://support.payhere.lk, Checkout API).
"""

import hashlib
import hmac
from dataclasses import dataclass

from app.config import settings

SANDBOX_URL = "https://sandbox.payhere.lk/pay/checkout"
LIVE_URL = "https://www.payhere.lk/pay/checkout"

# The gateway's own words for what happened to a payment.
STATUS_SUCCESS = "2"
STATUS_PENDING = "0"
STATUS_CANCELLED = "-1"
STATUS_FAILED = "-2"
STATUS_CHARGEBACK = "-3"


def _upper_md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest().upper()  # noqa: S324 -- this is PayHere's own scheme


def is_configured() -> bool:
    return bool(settings.payhere_merchant_id and settings.payhere_merchant_secret)


def checkout_url() -> str:
    return SANDBOX_URL if settings.payhere_mode == "sandbox" else LIVE_URL


def format_amount(whole_lkr: int) -> str:
    """PayHere wants two decimal places even though the shop's prices are whole rupees."""
    return f"{whole_lkr}.00"


def checkout_hash(order_id: str, amount: int, currency: str = "LKR") -> str:
    """The `hash` field of the checkout form: proves the amount was set by the server, not the
    browser."""
    secret_digest = _upper_md5(settings.payhere_merchant_secret or "")
    return _upper_md5(
        f"{settings.payhere_merchant_id}{order_id}{format_amount(amount)}{currency}{secret_digest}"
    )


@dataclass(frozen=True)
class NotifyPayload:
    merchant_id: str
    order_id: str
    payment_id: str
    payhere_amount: str
    payhere_currency: str
    status_code: str
    md5sig: str
    method: str | None = None
    status_message: str | None = None


def verify_notify(payload: NotifyPayload) -> bool:
    """Whether `md5sig` really was produced by PayHere with our merchant secret.

    Never trusts a notification without checking this first: it is the only thing that stops
    anyone who finds the notify URL from marking their own order as paid.
    """
    if not is_configured() or payload.merchant_id != settings.payhere_merchant_id:
        return False
    secret_digest = _upper_md5(settings.payhere_merchant_secret or "")
    expected = _upper_md5(
        f"{payload.merchant_id}{payload.order_id}{payload.payhere_amount}"
        f"{payload.payhere_currency}{payload.status_code}{secret_digest}"
    )
    # A constant-time comparison, so a timing difference cannot leak how much of the hash matched.
    return hmac.compare_digest(expected, payload.md5sig.upper())
