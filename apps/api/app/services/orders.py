"""Pricing and order creation. Every amount is computed here from the database."""

import hashlib
import json
import secrets
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.checkout_data import calculate_shipping
from app.config import settings
from app.models import Order, OrderItem, Product, User
from app.schemas_orders import OrderIn, OrderItemIn

# No 0, 1, I, L or O, so references are easy to read out over the phone.
_REFERENCE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_REFERENCE_LENGTH = 8
_MAX_REFERENCE_ATTEMPTS = 5


class InvalidCartError(Exception):
    """A line of the cart cannot be ordered: unknown product or a size the product lacks."""

    def __init__(self, index: int, field: str, message: str) -> None:
        super().__init__(message)
        self.index = index
        self.field = field
        self.message = message


class IdempotencyConflictError(Exception):
    """The Idempotency-Key was already used for a different request."""


@dataclass(frozen=True)
class PricedLine:
    product: Product
    size: str
    quantity: int

    @property
    def unit_price(self) -> int:
        return self.product.price

    @property
    def total(self) -> int:
        return self.product.price * self.quantity


@dataclass(frozen=True)
class Totals:
    subtotal: int
    shipping: int
    total: int


def price_items(db: Session, items: list[OrderItemIn]) -> list[PricedLine]:
    """Looks up each line in the catalogue. Prices always come from the database."""
    ids = {item.product_id for item in items}
    products = {
        product.id: product
        for product in db.scalars(
            select(Product).options(selectinload(Product.sizes)).where(Product.id.in_(ids))
        )
    }

    lines: list[PricedLine] = []
    for index, item in enumerate(items):
        product = products.get(item.product_id)
        if product is None:
            raise InvalidCartError(index, "productId", "This product does not exist.")
        if item.size not in {size.label for size in product.sizes}:
            raise InvalidCartError(index, "size", "This size is not available for the product.")
        lines.append(PricedLine(product=product, size=item.size, quantity=item.quantity))
    return lines


def compute_totals(lines: list[PricedLine], delivery_method: str) -> Totals:
    subtotal = sum(line.total for line in lines)
    shipping = calculate_shipping(subtotal, delivery_method)
    return Totals(subtotal=subtotal, shipping=shipping, total=subtotal + shipping)


def _new_reference() -> str:
    code = "".join(secrets.choice(_REFERENCE_ALPHABET) for _ in range(_REFERENCE_LENGTH))
    return f"{settings.order_reference_prefix}-{code}"


def _fingerprint(data: OrderIn) -> str:
    """Identifies the exact request, so a reused Idempotency-Key with other data is caught."""
    canonical = json.dumps(data.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _replay(existing: Order, fingerprint: str, user: User | None) -> Order:
    owner_id = user.id if user else None
    if existing.request_fingerprint != fingerprint or existing.user_id != owner_id:
        raise IdempotencyConflictError
    return existing


def create_order(
    db: Session, data: OrderIn, user: User | None, idempotency_key: str | None
) -> tuple[Order, bool]:
    """Creates an order and returns it with True, or returns the original with False on a retry."""
    fingerprint = _fingerprint(data)

    if idempotency_key:
        existing = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
        if existing:
            return _replay(existing, fingerprint, user), False

    lines = price_items(db, data.items)
    totals = compute_totals(lines, data.delivery_method)

    for _ in range(_MAX_REFERENCE_ATTEMPTS):
        order = Order(
            reference=_new_reference(),
            user_id=user.id if user else None,
            email=data.email,
            phone=data.phone,
            full_name=data.full_name,
            address1=data.address1,
            address2=data.address2,
            city=data.city,
            province=data.province,
            district=data.district,
            postal_code=data.postal_code,
            delivery_method=data.delivery_method,
            payment_method=data.payment_method,
            subtotal=totals.subtotal,
            shipping=totals.shipping,
            total=totals.total,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            items=[
                OrderItem(
                    product_id=line.product.id,
                    product_name=line.product.name,
                    colour=line.product.colour,
                    size=line.size,
                    unit_price=line.unit_price,
                    quantity=line.quantity,
                    line_total=line.total,
                    position=position,
                )
                for position, line in enumerate(lines)
            ],
        )
        try:
            with db.begin_nested():
                db.add(order)
        except IntegrityError:
            # Either the reference collided (try another) or a parallel request with the same
            # Idempotency-Key won the race (return its order).
            if idempotency_key:
                winner = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
                if winner:
                    return _replay(winner, fingerprint, user), False
            continue
        db.commit()
        return order, True

    raise RuntimeError("Could not allocate an order reference")


def list_orders(db: Session, user: User, *, page: int, page_size: int) -> tuple[list[Order], int]:
    total = db.scalar(select(func.count()).select_from(Order).where(Order.user_id == user.id)) or 0
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(orders), total


def get_user_order(db: Session, user: User, reference: str) -> Order | None:
    """An order, but only when it belongs to this user."""
    return db.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.reference == reference, Order.user_id == user.id)
    )
