from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response
from sqlalchemy.orm import Session

from app import payhere
from app.api.deps import PaginationDep, TrustedOrigin, UserDep, cart_problem, current_user
from app.db import get_db
from app.models import User
from app.schemas import Page
from app.schemas_orders import OrderIn, OrderOut, OrderStatusOut
from app.services import orders

router = APIRouter(prefix="/orders", tags=["orders"])

DbDep = Annotated[Session, Depends(get_db)]


@router.post("", status_code=201, response_model=OrderOut, dependencies=[TrustedOrigin])
def create_order(
    body: OrderIn,
    response: Response,
    db: DbDep,
    user: Annotated[User | None, Depends(current_user)],
    idempotency_key: Annotated[
        str | None, Header(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    ] = None,
) -> OrderOut:
    """Places an order. Prices, shipping and the total are always worked out on the server."""
    if body.payment_method == "card" and not payhere.is_configured():
        raise HTTPException(
            status_code=422,
            detail={
                "code": "payment_method_unavailable",
                "message": "Card payment is not available right now. Please choose another method.",
            },
        )
    try:
        order, created = orders.create_order(db, body, user, idempotency_key)
    except orders.InvalidCartError as error:
        raise cart_problem(error) from error
    except orders.PriceChangedError as error:
        # The current total is included so the website can show it and let the shopper decide.
        raise HTTPException(
            status_code=409,
            detail={
                "code": "price_changed",
                "message": "The price of your order has changed. Please review the new total.",
                "total": error.total,
            },
        ) from error
    except orders.IdempotencyConflictError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "idempotency_conflict",
                "message": "This Idempotency-Key was already used for a different order",
            },
        ) from error

    if not created:
        response.status_code = 200  # a retry gets the original order back
    response.headers["Cache-Control"] = "no-store"
    out = OrderOut.from_order(order)
    # A retry (same Idempotency-Key) still gets the form: the shopper has not paid yet and still
    # needs to reach PayHere. Only a later GET of the order leaves it out.
    out.payhere = orders.build_payhere_checkout(order)
    return out


@router.get("", response_model=Page[OrderOut])
def list_my_orders(user: UserDep, db: DbDep, pagination: PaginationDep) -> Page[OrderOut]:
    found, total = orders.list_orders(
        db, user, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[OrderOut.from_order(order) for order in found],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{reference}/status", response_model=OrderStatusOut)
def get_order_status(
    reference: Annotated[str, Path(max_length=20)], db: DbDep, response: Response
) -> OrderStatusOut:
    order = orders.get_order_status(db, reference)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    response.headers["Cache-Control"] = "no-store"
    return OrderStatusOut(status=order.status, payment_status=order.payment_status)


@router.get("/{reference}", response_model=OrderOut)
def get_my_order(
    reference: Annotated[str, Path(max_length=20)], user: UserDep, db: DbDep, response: Response
) -> OrderOut:
    order = orders.get_user_order(db, user, reference)
    if order is None:
        # The same answer for a missing order and someone else's, so references cannot be probed.
        raise HTTPException(status_code=404, detail="Order not found")
    response.headers["Cache-Control"] = "no-store"
    return OrderOut.from_order(order)
