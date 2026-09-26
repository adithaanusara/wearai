from datetime import datetime
from typing import Any, Literal

from app.schemas import CamelModel
from app.schemas_orders import StrictModel


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
