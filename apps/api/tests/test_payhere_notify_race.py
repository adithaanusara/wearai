"""A real race on separate connections. Two identical notifications for the same order arrive at
the same moment; only one may end up recorded as a real change.

A small delay is injected between the read and the write so the window is wide enough to hit
reliably (the two database calls involved are otherwise too quick to overlap on a fast local
database) - it does not change what is being tested, only how likely it is to be observed.
"""

import hashlib
import threading
import time

import pytest
from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session

from app import payhere
from app.config import settings
from app.models import Order, PaymentEvent
from app.services import payments

MERCHANT_ID = "1211149"
SECRET = "test-secret"
REFERENCE = "WA-RACEPAY1"


def notify_payload() -> payhere.NotifyPayload:
    secret_digest = hashlib.md5(SECRET.encode()).hexdigest().upper()  # noqa: S324
    status_code = payhere.STATUS_SUCCESS
    md5sig = (
        hashlib.md5(  # noqa: S324
            f"{MERCHANT_ID}{REFERENCE}1000.00LKR{status_code}{secret_digest}".encode()
        )
        .hexdigest()
        .upper()
    )
    return payhere.NotifyPayload(
        merchant_id=MERCHANT_ID,
        order_id=REFERENCE,
        payment_id="pay-1",
        payhere_amount="1000.00",
        payhere_currency="LKR",
        status_code=status_code,
        md5sig=md5sig,
    )


def test_two_identical_notifications_at_the_same_moment_produce_only_one_real_change(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "payhere_merchant_id", MERCHANT_ID)
    monkeypatch.setattr(settings, "payhere_merchant_secret", SECRET)
    # Widens the window between the locked read and the write, so two real, separate database
    # connections have time to overlap there if (and only if) the read did not actually lock the
    # row.
    monkeypatch.setattr(payments, "_status_for", lambda code: (time.sleep(0.2), "paid")[1])

    with Session(engine) as setup:
        setup.add(
            Order(
                reference=REFERENCE,
                email="r@example.com",
                phone="0771234567",
                full_name="R",
                address1="a",
                city="c",
                province="Western",
                district="Colombo",
                postal_code="10250",
                delivery_method="standard",
                payment_method="card",
                subtotal=1000,
                shipping=0,
                total=1000,
            )
        )
        setup.commit()

    start = threading.Barrier(2)

    def act() -> None:
        with Session(engine) as session:
            start.wait()
            payments.handle_notify(session, notify_payload())

    try:
        threads = [threading.Thread(target=act) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        with Session(engine) as check:
            order = check.scalar(select(Order).where(Order.reference == REFERENCE))
            events = check.scalars(
                select(PaymentEvent).where(PaymentEvent.order_id == order.id)
            ).all()
        assert order.payment_status == "paid"
        real_changes = [e for e in events if e.source == "payhere_notify"]
        replays = [e for e in events if e.source == "payhere_notify_replay"]
        assert len(real_changes) == 1, "both notifications read the order as unpaid and both wrote"
        assert len(replays) == 1
    finally:
        with Session(engine) as cleanup:
            cleanup.execute(delete(Order).where(Order.reference == REFERENCE))
            cleanup.commit()
