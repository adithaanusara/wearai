from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from app.schemas import CamelModel
from app.schemas_orders import MAX_MONEY, OrderOut, StrictModel


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
    payment_status: str
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


class PaymentEventOut(CamelModel):
    from_status: str
    to_status: str
    source: str
    method: str | None
    message: str | None
    created_at: datetime


class AdminOrderOut(OrderOut):
    history: list[StatusHistoryOut]
    allowed_next: list[str]
    payment_events: list[PaymentEventOut]


class AdminImageOut(CamelModel):
    id: int
    url: str


class AdminProductOut(CamelModel):
    id: str
    slug: str
    name: str
    colour: str
    gender: str
    category: str
    price: int
    compare_at_price: int | None
    description: str
    images: list[AdminImageOut]
    sizes: list[str]
    archived: bool
    updated_at: datetime


class ProductEditIn(StrictModel):
    """Every editable field is sent each time, with the version (`updatedAt`) it is based on."""

    updated_at: datetime
    name: str
    price: int = Field(ge=0, le=MAX_MONEY, strict=True)
    compare_at_price: int | None = Field(ge=0, le=MAX_MONEY, strict=True)
    description: str

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 120:
            raise ValueError("Enter a name of up to 120 characters.")
        return value

    @field_validator("description")
    @classmethod
    def _description(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 2000:
            raise ValueError("Enter a description of up to 2,000 characters.")
        return value

    @model_validator(mode="after")
    def _compare_at_above_price(self) -> "ProductEditIn":
        if self.compare_at_price is not None and self.compare_at_price <= self.price:
            raise ValueError("The compare-at price must be higher than the price.")
        return self


class ProductVersionIn(StrictModel):
    """Archive and restore also say which version they were based on."""

    updated_at: datetime


class ImageOrderIn(StrictModel):
    """The images in their new order, with the product version the admin was looking at."""

    updated_at: datetime
    image_ids: list[int] = Field(min_length=1, max_length=8)
