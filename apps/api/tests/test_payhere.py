"""The hash math on its own, checked against a value worked out by hand from PayHere's formula."""

import hashlib

import pytest

from app import payhere
from app.config import settings


@pytest.fixture(autouse=True)
def credentials(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "payhere_merchant_id", "1211149")
    monkeypatch.setattr(settings, "payhere_merchant_secret", "MjgxNDQ2ODIxNjA1NTM2Mzg3Njcw")
    monkeypatch.setattr(settings, "payhere_mode", "sandbox")


def by_hand(merchant_id: str, order_id: str, amount: str, currency: str, status_code: str) -> str:
    secret_digest = hashlib.md5(settings.payhere_merchant_secret.encode()).hexdigest().upper()  # noqa: S324
    return (
        hashlib.md5(  # noqa: S324
            f"{merchant_id}{order_id}{amount}{currency}{status_code}{secret_digest}".encode()
        )
        .hexdigest()
        .upper()
    )


def test_is_configured_needs_both_values(monkeypatch: pytest.MonkeyPatch) -> None:
    assert payhere.is_configured()
    monkeypatch.setattr(settings, "payhere_merchant_secret", None)
    assert not payhere.is_configured()
    monkeypatch.setattr(settings, "payhere_merchant_secret", "x")
    monkeypatch.setattr(settings, "payhere_merchant_id", None)
    assert not payhere.is_configured()


def test_checkout_url_follows_the_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    assert payhere.checkout_url() == "https://sandbox.payhere.lk/pay/checkout"
    monkeypatch.setattr(settings, "payhere_mode", "live")
    assert payhere.checkout_url() == "https://www.payhere.lk/pay/checkout"


def test_amount_always_has_two_decimal_places() -> None:
    assert payhere.format_amount(1000) == "1000.00"
    assert payhere.format_amount(0) == "0.00"


def test_checkout_hash_matches_the_formula_worked_out_by_hand() -> None:
    computed = payhere.checkout_hash("WA-ABC12345", 6900)

    # Built directly from PayHere's formula (no status_code term for the checkout hash), so it
    # does not depend on `by_hand`, which is used for the notify hash below.
    secret_digest = hashlib.md5(settings.payhere_merchant_secret.encode()).hexdigest().upper()  # noqa: S324
    expected = (
        hashlib.md5(  # noqa: S324
            f"1211149WA-ABC123456900.00LKR{secret_digest}".encode()
        )
        .hexdigest()
        .upper()
    )

    assert computed == expected
    assert computed.isupper() and len(computed) == 32


def test_a_different_amount_or_order_changes_the_hash() -> None:
    base = payhere.checkout_hash("WA-ABC12345", 6900)

    assert payhere.checkout_hash("WA-ABC12345", 6901) != base
    assert payhere.checkout_hash("WA-ABC99999", 6900) != base
    assert payhere.checkout_hash("WA-ABC12345", 6900, currency="USD") != base


def notify(**overrides) -> payhere.NotifyPayload:
    values = {
        "merchant_id": "1211149",
        "order_id": "WA-ABC12345",
        "payment_id": "320012345678",
        "payhere_amount": "6900.00",
        "payhere_currency": "LKR",
        "status_code": payhere.STATUS_SUCCESS,
        "md5sig": "",
        "method": "VISA",
        "status_message": "Approved",
    }
    values.update(overrides)
    if not values["md5sig"]:
        values["md5sig"] = by_hand(
            values["merchant_id"],
            values["order_id"],
            values["payhere_amount"],
            values["payhere_currency"],
            values["status_code"],
        )
    return payhere.NotifyPayload(**values)


def test_verify_notify_accepts_a_correctly_signed_payload() -> None:
    assert payhere.verify_notify(notify())


@pytest.mark.parametrize(
    "field",
    ["merchant_id", "order_id", "payhere_amount", "payhere_currency", "status_code"],
)
def test_verify_notify_rejects_any_changed_field(field: str) -> None:
    payload = notify()
    changed = payhere.NotifyPayload(**{**vars(payload), field: vars(payload)[field] + "x"})

    assert not payhere.verify_notify(changed)


def test_verify_notify_rejects_a_forged_signature() -> None:
    assert not payhere.verify_notify(notify(md5sig="0" * 32))


def test_verify_notify_is_case_insensitive_on_the_signature() -> None:
    payload = notify()
    lower = payhere.NotifyPayload(**{**vars(payload), "md5sig": payload.md5sig.lower()})

    assert payhere.verify_notify(lower)


def test_verify_notify_rejects_the_wrong_merchant(monkeypatch: pytest.MonkeyPatch) -> None:
    assert not payhere.verify_notify(notify(merchant_id="9999999"))


def test_verify_notify_refuses_everything_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "payhere_merchant_secret", None)
    assert not payhere.verify_notify(notify(md5sig="0" * 32))
