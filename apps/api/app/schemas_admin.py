from datetime import datetime
from typing import Any, Literal

from app.schemas import CamelModel
from app.schemas_orders import OrderOut, StrictModel


class AdminUserOut(CamelModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime


class RoleChangeIn(StrictModel):
    role: Literal["customer", "staff", "admin"]


class AuditEntryOut(CamelModel):
    id: int
    created_at: datetime
    actor_email: str
    action: str
    entity: str
    entity_id: str
    details: dict[str, Any]


class DashboardOut(CamelModel):
    orders_by_status: dict[str, int]
    products: int
    customers: int


class OrderSummaryOut(CamelModel):
    reference: str
    status: str
    email: str
    full_name: str
    total: int
    created_at: datetime


class StatusChangeIn(StrictModel):
    """The status the caller saw and the one they want, so a stale screen cannot overwrite."""

    expected_status: Literal["pending", "confirmed", "shipped", "delivered", "cancelled"]
    status: Literal["pending", "confirmed", "shipped", "delivered", "cancelled"]


class StatusHistoryOut(CamelModel):
    from_status: str
    to_status: str
    actor_email: str
    created_at: datetime


class AdminOrderOut(OrderOut):
    history: list[StatusHistoryOut]
    allowed_next: list[str]
