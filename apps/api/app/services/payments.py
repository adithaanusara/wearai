"""Handles PayHere's payment notification (the webhook), and reads an order's payment history.

The webhook is the only thing that ever moves an order from unpaid to paid or failed: no admin
action does it, because only PayHere actually knows whether the money arrived.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import payhere
from app.models import Order, PaymentEvent

# Once paid, a payment never falls back to pending or unpaid; a chargeback (reported as "failed"
# here, since the shop does not distinguish it) is the only way a paid order's status changes again.
_FINAL = {"paid"}


class NotifyRejectedError(Exception):
    """The notification's signature does not check out, or names an order we do not have."""


def _status_for(status_code: str) -> str:
    if status_code == payhere.STATUS_SUCCESS:
        return "paid"
    if status_code == payhere.STATUS_PENDING:
        return "pending"
    return "failed"  # cancelled or failed or charged back: no money is with us


def handle_notify(db: Session, payload: payhere.NotifyPayload) -> Order:
    """Applies a verified PayHere notification. Raises `NotifyRejectedError` for anything else."""
    if not payhere.verify_notify(payload):
        raise NotifyRejectedError("Signature did not match.")

    order = db.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.reference == payload.order_id)
        .with_for_update()
    )
    if order is None:
        raise NotifyRejectedError("No such order.")

    new_status = _status_for(payload.status_code)
    if order.payment_status in _FINAL:
        # A paid order does not go back to pending on a late or resent notification. A genuine
        # chargeback still records as an event, just without changing what is already paid.
        db.add(
            PaymentEvent(
                order_id=order.id,
                from_status=order.payment_status,
                to_status=order.payment_status,
                source="payhere_notify_replay",
                method=payload.method,
                message=payload.status_message,
            )
        )
        db.commit()
        return order

    previous = order.payment_status
    order.payment_status = new_status
    order.payhere_payment_id = payload.payment_id
    db.add(
        PaymentEvent(
            order_id=order.id,
            from_status=previous,
            to_status=new_status,
            source="payhere_notify",
            method=payload.method,
            message=payload.status_message,
        )
    )
    db.commit()
    return order


def events_for(db: Session, order: Order) -> list[PaymentEvent]:
    return list(
        db.scalars(
            select(PaymentEvent).where(PaymentEvent.order_id == order.id).order_by(PaymentEvent.id)
        )
    )
