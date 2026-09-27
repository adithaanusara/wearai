"""The notify webhook: only a genuinely signed report from PayHere ever changes an order."""

import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import payhere
from app.config import settings
from app.models import Order, PaymentEvent
from tests.helpers import place_order

pytestmark = pytest.mark.usefixtures("catalogue")

NOTIFY = "/api/v1/payments/payhere/notify"
MERCHANT_ID = "1211149"
SECRET = "test-secret"


@pytest.fixture(autouse=True)
def payhere_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "payhere_merchant_id", MERCHANT_ID)
    monkeypatch.setattr(settings, "payhere_merchant_secret", SECRET)


def signed_form(order, status_code: str, **overrides) -> dict:
    amount = payhere.format_amount(order.total)
    secret_digest = hashlib.md5(SECRET.encode()).hexdigest().upper()  # noqa: S324
    md5sig = (
        hashlib.md5(  # noqa: S324
            f"{MERCHANT_ID}{order.reference}{amount}LKR{status_code}{secret_digest}".encode()
        )
        .hexdigest()
        .upper()
    )
    form = {
        "merchant_id": MERCHANT_ID,
        "order_id": order.reference,
        "payment_id": "320099999999",
        "payhere_amount": amount,
        "payhere_currency": "LKR",
        "status_code": status_code,
        "md5sig": md5sig,
        "method": "VISA",
        "status_message": "Two Party Mandate Fulfilled",
    }
    form.update(overrides)
    return form


def place_card_order(client: TestClient, db: Session, **overrides) -> Order:
    reference = place_order(client, paymentMethod="card", **overrides).json()["reference"]
    return db.scalar(select(Order).where(Order.reference == reference))


def test_a_genuine_success_notification_marks_the_order_paid(
    client: TestClient, db: Session
) -> None:
    order = place_card_order(client, db)

    response = client.post(NOTIFY, data=signed_form(order, payhere.STATUS_SUCCESS))

    assert response.status_code == 200
    db.refresh(order)
    assert order.payment_status == "paid"
    assert order.payhere_payment_id == "320099999999"
    event = db.scalars(select(PaymentEvent).where(PaymentEvent.order_id == order.id)).one()
    assert (event.from_status, event.to_status, event.source, event.method) == (
        "unpaid",
        "paid",
        "payhere_notify",
        "VISA",
    )


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (payhere.STATUS_PENDING, "pending"),
        (payhere.STATUS_CANCELLED, "failed"),
        (payhere.STATUS_FAILED, "failed"),
    ],
)
def test_other_outcomes_are_recorded_as_they_are_reported(
    client: TestClient, db: Session, status_code: str, expected: str
) -> None:
    order = place_card_order(client, db)

    client.post(NOTIFY, data=signed_form(order, status_code))

    db.refresh(order)
    assert order.payment_status == expected


def test_a_forged_signature_changes_nothing(client: TestClient, db: Session) -> None:
    order = place_card_order(client, db)

    response = client.post(NOTIFY, data=signed_form(order, payhere.STATUS_SUCCESS, md5sig="0" * 32))

    assert response.status_code == 200  # PayHere is told OK regardless; it would only retry
    db.refresh(order)
    assert order.payment_status == "unpaid"
    assert db.scalars(select(PaymentEvent)).first() is None


def test_a_tampered_amount_is_rejected_even_with_a_matching_looking_signature(
    client: TestClient, db: Session
) -> None:
    order = place_card_order(client, db)
    form = signed_form(order, payhere.STATUS_SUCCESS)
    form["payhere_amount"] = payhere.format_amount(
        1
    )  # changed after signing, so the sig no longer matches

    client.post(NOTIFY, data=form)

    db.refresh(order)
    assert order.payment_status == "unpaid"


def test_a_notification_for_an_unknown_order_is_ignored(client: TestClient, db: Session) -> None:
    order = place_card_order(client, db)
    form = signed_form(order, payhere.STATUS_SUCCESS)
    secret_digest = hashlib.md5(SECRET.encode()).hexdigest().upper()  # noqa: S324
    form["order_id"] = "WA-NOSUCH1"
    form["md5sig"] = (
        hashlib.md5(  # noqa: S324
            f"{MERCHANT_ID}WA-NOSUCH1{form['payhere_amount']}LKR{payhere.STATUS_SUCCESS}{secret_digest}".encode()
        )
        .hexdigest()
        .upper()
    )

    response = client.post(NOTIFY, data=form)

    assert response.status_code == 200
    assert db.scalars(select(PaymentEvent)).first() is None


def test_a_repeated_success_notification_does_not_duplicate_the_event(
    client: TestClient, db: Session
) -> None:
    order = place_card_order(client, db)
    form = signed_form(order, payhere.STATUS_SUCCESS)

    client.post(NOTIFY, data=form)
    client.post(NOTIFY, data=form)

    db.refresh(order)
    assert order.payment_status == "paid"
    events = db.scalars(select(PaymentEvent).where(PaymentEvent.order_id == order.id)).all()
    assert [e.source for e in events] == ["payhere_notify", "payhere_notify_replay"]


def test_a_paid_order_cannot_be_pushed_back_to_pending_by_a_late_notification(
    client: TestClient, db: Session
) -> None:
    order = place_card_order(client, db)
    client.post(NOTIFY, data=signed_form(order, payhere.STATUS_SUCCESS))

    client.post(NOTIFY, data=signed_form(order, payhere.STATUS_PENDING))

    db.refresh(order)
    assert order.payment_status == "paid"


def test_a_missing_field_is_a_422_and_changes_nothing(client: TestClient, db: Session) -> None:
    order = place_card_order(client, db)
    form = signed_form(order, payhere.STATUS_SUCCESS)
    del form["md5sig"]

    response = client.post(NOTIFY, data=form)

    assert response.status_code == 422
    db.refresh(order)
    assert order.payment_status == "unpaid"


def test_the_notify_route_does_not_require_a_trusted_origin(
    client: TestClient, db: Session
) -> None:
    """PayHere calls this directly; it is not a browser request and sends no Origin header."""
    order = place_card_order(client, db)

    response = client.post(
        NOTIFY,
        data=signed_form(order, payhere.STATUS_SUCCESS),
        headers={"Origin": "https://sandbox.payhere.lk"},
    )

    assert response.status_code == 200
    db.refresh(order)
    assert order.payment_status == "paid"


def test_a_cod_orders_payment_status_is_untouched_by_notify(
    client: TestClient, db: Session
) -> None:
    reference = place_order(client, paymentMethod="cod").json()["reference"]
    order = db.scalar(select(Order).where(Order.reference == reference))

    client.post(NOTIFY, data=signed_form(order, payhere.STATUS_SUCCESS))

    db.refresh(order)
    assert order.payment_status == "paid"  # the webhook does not know or care which method it was
