"""Order management for staff. Prices and lines are never changed here, only the status."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Order, OrderStatusHistory, User
from app.services import audit
from app.services.admin import AdminError, like_pattern

# The only moves allowed. Delivered and cancelled are final, and a shipped order cannot be
# cancelled: it is already on its way, so a return is a separate process.
TRANSITIONS: dict[str, tuple[str, ...]] = {
    "pending": ("confirmed", "cancelled"),
    "confirmed": ("shipped", "cancelled"),
    "shipped": ("delivered",),
    "delivered": (),
    "cancelled": (),
}


def allowed_next(status: str) -> list[str]:
    return list(TRANSITIONS.get(status, ()))


def list_orders(
    db: Session, *, status: str | None, search: str | None, page: int, page_size: int
) -> tuple[list[Order], int]:
    conditions = []
    if status:
        conditions.append(Order.status == status)
    if search and search.strip():
        pattern = like_pattern(search.strip())
        conditions.append(
            or_(
                Order.reference.ilike(pattern, escape="\\"),
                Order.email.ilike(pattern, escape="\\"),
                Order.full_name.ilike(pattern, escape="\\"),
            )
        )
    total = db.scalar(select(func.count()).select_from(Order).where(*conditions)) or 0
    orders = db.scalars(
        select(Order)
        .where(*conditions)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(orders), total


def get_order(db: Session, reference: str) -> Order | None:
    return db.scalar(
        select(Order).options(selectinload(Order.items)).where(Order.reference == reference)
    )


def history_for(db: Session, order: Order) -> list[OrderStatusHistory]:
    return list(
        db.scalars(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order.id)
            .order_by(OrderStatusHistory.id)
        )
    )


def change_status(
    db: Session, *, actor: User, reference: str, expected_status: str, new_status: str
) -> Order:
    """Moves an order to its next status.

    The caller says which status they saw. If someone else has changed it since, nothing happens
    and they are told to reload, so two people cannot overwrite each other unknowingly.
    """
    # The row is locked until the end of the transaction, so two changes cannot interleave.
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.reference == reference)
        .with_for_update()
    )
    if order is None:
        raise AdminError(404, "Order not found.")
    if order.status != expected_status:
        raise AdminError(
            409,
            "This order was changed by someone else. Reload to see its current status.",
            code="stale_status",
            status=order.status,
        )
    if new_status not in TRANSITIONS[order.status]:
        raise AdminError(
            409,
            f"An order that is {order.status} cannot be moved to {new_status}.",
            code="invalid_transition",
            status=order.status,
        )

    previous = order.status
    order.status = new_status
    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=previous,
            to_status=new_status,
            actor_id=actor.id,
            actor_email=actor.email,
        )
    )
    audit.record(
        db,
        actor=actor,
        action="order.status_changed",
        entity="order",
        entity_id=order.reference,
        details={"from": previous, "to": new_status},
    )
    db.commit()
    return order
