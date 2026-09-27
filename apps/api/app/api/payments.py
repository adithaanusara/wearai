"""The public side of payments: PayHere's server-to-server notification.

Unlike every other route in this API, this one is never called by our own website: PayHere calls
it directly, so there is no session, no Origin header to trust, and no CSRF concern (there is
nothing here a browser could be tricked into doing). What stands in for authentication is the
notification's own signature, checked in `app.services.payments`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app import payhere
from app.db import get_db
from app.services import payments

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/payhere/notify")
def payhere_notify(
    db: Annotated[Session, Depends(get_db)],
    merchant_id: Annotated[str, Form()],
    order_id: Annotated[str, Form()],
    payment_id: Annotated[str, Form()],
    payhere_amount: Annotated[str, Form()],
    payhere_currency: Annotated[str, Form()],
    status_code: Annotated[str, Form()],
    md5sig: Annotated[str, Form()],
    method: Annotated[str | None, Form()] = None,
    status_message: Annotated[str | None, Form()] = None,
) -> PlainTextResponse:
    """Always answers 200: PayHere retries on anything else, which would not help here."""
    payload = payhere.NotifyPayload(
        merchant_id=merchant_id,
        order_id=order_id,
        payment_id=payment_id,
        payhere_amount=payhere_amount,
        payhere_currency=payhere_currency,
        status_code=status_code,
        md5sig=md5sig,
        method=method,
        status_message=status_message,
    )
    try:
        payments.handle_notify(db, payload)
    except payments.NotifyRejectedError:
        db.rollback()
    return PlainTextResponse("OK")
