from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response
from sqlalchemy.orm import Session

from app.api.deps import PaginationDep, TrustedOrigin, UserDep, cart_problem, current_user
from app.db import get_db
from app.models import User
from app.schemas import Page
from app.schemas_orders import OrderIn, OrderOut
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
    try:
        order, created = orders.create_order(db, body, user, idempotency_key)
    except orders.InvalidCartError as error:
        raise cart_problem(error) from error
    except orders.IdempotencyConflictError as error:
        raise HTTPException(
            status_code=409, detail="This Idempotency-Key was already used for a different order"
        ) from error

    if not created:
        response.status_code = 200  # a retry gets the original order back
    response.headers["Cache-Control"] = "no-store"
    return OrderOut.from_order(order)


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
