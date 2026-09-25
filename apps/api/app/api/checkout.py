from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import cart_problem
from app.checkout_data import DELIVERY_METHODS, PAYMENT_METHODS, PROVINCES
from app.db import get_db
from app.schemas_orders import (
    CheckoutOptionsOut,
    DeliveryMethodOut,
    LineOut,
    PaymentMethodOut,
    ProvinceOut,
    QuoteIn,
    QuoteOut,
)
from app.services import orders

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.get("/options", response_model=CheckoutOptionsOut)
def options() -> CheckoutOptionsOut:
    """What the checkout form offers, so the website does not have to hard-code it."""
    return CheckoutOptionsOut(
        delivery_methods=[
            DeliveryMethodOut(
                id=m.id, label=m.label, estimate=m.estimate, fee=m.fee, free_over=m.free_over
            )
            for m in DELIVERY_METHODS.values()
        ],
        payment_methods=[
            PaymentMethodOut(id=m.id, label=m.label, note=m.note) for m in PAYMENT_METHODS.values()
        ],
        provinces=[ProvinceOut(name=name, districts=d) for name, d in PROVINCES.items()],
    )


@router.post("/quote", response_model=QuoteOut)
def quote(body: QuoteIn, db: Annotated[Session, Depends(get_db)]) -> QuoteOut:
    """Prices a cart without creating anything."""
    try:
        lines = orders.price_items(db, body.items)
    except orders.InvalidCartError as error:
        raise cart_problem(error) from error

    totals = orders.compute_totals(lines, body.delivery_method)
    return QuoteOut(
        lines=[
            LineOut(
                product_id=line.product.id,
                name=line.product.name,
                colour=line.product.colour,
                size=line.size,
                unit_price=line.unit_price,
                quantity=line.quantity,
                line_total=line.total,
            )
            for line in lines
        ],
        subtotal=totals.subtotal,
        shipping=totals.shipping,
        total=totals.total,
    )
