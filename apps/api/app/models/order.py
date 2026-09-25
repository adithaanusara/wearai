from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

ORDER_STATUSES = ("pending", "confirmed", "shipped", "delivered", "cancelled")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')",
            name="ck_orders_status",
        ),
        CheckConstraint("subtotal >= 0 AND shipping >= 0", name="ck_orders_money_non_negative"),
        CheckConstraint("total = subtotal + shipping", name="ck_orders_total_adds_up"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True)
    # Guests can check out, so an order does not always belong to an account.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")

    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(120))
    address1: Mapped[str] = mapped_column(String(200))
    address2: Mapped[str] = mapped_column(String(200), default="")
    city: Mapped[str] = mapped_column(String(80))
    province: Mapped[str] = mapped_column(String(40))
    district: Mapped[str] = mapped_column(String(40))
    postal_code: Mapped[str] = mapped_column(String(5))

    delivery_method: Mapped[str] = mapped_column(String(20))
    payment_method: Mapped[str] = mapped_column(String(20))

    # Whole LKR. The server computes these; the browser never supplies them.
    subtotal: Mapped[int] = mapped_column(Integer)
    shipping: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)

    # Lets a retried request return the original order instead of creating a second one.
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    items: Mapped[list["OrderItem"]] = relationship(
        order_by="OrderItem.position", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """A line of an order. Name, colour and price are copied so history never changes."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity BETWEEN 1 AND 10", name="ck_order_items_quantity_range"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_price_non_negative"),
        CheckConstraint("line_total = unit_price * quantity", name="ck_order_items_line_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    # RESTRICT keeps a product that has been ordered from being deleted out from under the history.
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(120))
    colour: Mapped[str] = mapped_column(String(40))
    size: Mapped[str] = mapped_column(String(20))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(SmallInteger)
    line_total: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(SmallInteger)
