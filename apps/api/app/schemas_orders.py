import re
from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field, ValidationInfo, field_validator
from pydantic.alias_generators import to_camel

from app.checkout_data import DELIVERY_METHODS, PAYMENT_METHODS, PROVINCES
from app.models import Order
from app.schemas import CamelModel

MAX_LINES = 50
MAX_MONEY = 100_000_000  # LKR; far above any real order, and rejects absurd input
# [0-9] rather than \d, because \d also matches digits from other scripts (such as fullwidth ones).
_PHONE = re.compile(
    r"^(?:\+94|0)(7[0-9]{8})$"
)  # Sri Lankan mobile: 07X XXX XXXX or +94 7X XXX XXXX
_POSTAL_CODE = re.compile(r"^[0-9]{5}$")


class StrictModel(CamelModel):
    """Request bodies reject unknown fields, so a tampered price or total is an error."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class OrderItemIn(StrictModel):
    product_id: str = Field(min_length=1, max_length=32)
    size: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=1, le=10, strict=True)


class QuoteIn(StrictModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=MAX_LINES)
    delivery_method: str

    @field_validator("delivery_method")
    @classmethod
    def _delivery_method(cls, value: str) -> str:
        if value not in DELIVERY_METHODS:
            raise ValueError("Select a delivery method.")
        return value

    @field_validator("items")
    @classmethod
    def _no_duplicate_lines(cls, items: list[OrderItemIn]) -> list[OrderItemIn]:
        keys = [(item.product_id, item.size) for item in items]
        if len(set(keys)) != len(keys):
            raise ValueError("Each product and size may appear only once.")
        return items


def _required_text(value: str, message: str, max_length: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError(message)
    if len(value) > max_length:
        raise ValueError(f"Use at most {max_length} characters.")
    return value


class OrderIn(QuoteIn):
    email: EmailStr
    phone: str
    full_name: str
    address1: str
    address2: str = ""
    city: str
    province: str
    district: str
    postal_code: str
    payment_method: str
    # The total the shopper was shown, in whole LKR. It is only compared with the real total and
    # never used as a price. Leaving it out skips the comparison.
    expected_total: int | None = Field(default=None, ge=0, le=MAX_MONEY, strict=True)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str) -> str:
        match = _PHONE.match(re.sub(r"[\s-]", "", value))
        if not match:
            raise ValueError("Enter a valid mobile number, like 077 123 4567.")
        return f"+94{match.group(1)}"

    @field_validator("full_name")
    @classmethod
    def _full_name(cls, value: str) -> str:
        return _required_text(value, "Enter your full name.", 120)

    @field_validator("address1")
    @classmethod
    def _address1(cls, value: str) -> str:
        return _required_text(value, "Enter your address.", 200)

    @field_validator("address2")
    @classmethod
    def _address2(cls, value: str) -> str:
        value = value.strip()
        if len(value) > 200:
            raise ValueError("Use at most 200 characters.")
        return value

    @field_validator("city")
    @classmethod
    def _city(cls, value: str) -> str:
        return _required_text(value, "Enter your city.", 80)

    @field_validator("province")
    @classmethod
    def _province(cls, value: str) -> str:
        if value not in PROVINCES:
            raise ValueError("Select a province.")
        return value

    @field_validator("postal_code")
    @classmethod
    def _postal_code(cls, value: str) -> str:
        value = value.strip()
        if not _POSTAL_CODE.match(value):
            raise ValueError("Enter a 5-digit postal code.")
        return value

    @field_validator("payment_method")
    @classmethod
    def _payment_method(cls, value: str) -> str:
        if value not in PAYMENT_METHODS:
            raise ValueError("Select a payment method.")
        return value

    @field_validator("district")
    @classmethod
    def _district(cls, value: str, info: ValidationInfo) -> str:
        # Fields are validated in order, so the province is already known here. If it was invalid
        # it is missing from info.data and no district can be right.
        if value not in PROVINCES.get(info.data.get("province", ""), []):
            raise ValueError("Select a district in the chosen province.")
        return value


class LineOut(CamelModel):
    product_id: str
    name: str
    colour: str
    size: str
    unit_price: int
    quantity: int
    line_total: int


class QuoteOut(CamelModel):
    lines: list[LineOut]
    subtotal: int
    shipping: int
    total: int


class OrderOut(CamelModel):
    reference: str
    status: str
    email: str
    phone: str
    full_name: str
    address1: str
    address2: str
    city: str
    province: str
    district: str
    postal_code: str
    delivery_method: str
    payment_method: str
    lines: list[LineOut]
    subtotal: int
    shipping: int
    total: int
    created_at: datetime

    @classmethod
    def from_order(cls, order: Order) -> "OrderOut":
        return cls(
            reference=order.reference,
            status=order.status,
            email=order.email,
            phone=order.phone,
            full_name=order.full_name,
            address1=order.address1,
            address2=order.address2,
            city=order.city,
            province=order.province,
            district=order.district,
            postal_code=order.postal_code,
            delivery_method=order.delivery_method,
            payment_method=order.payment_method,
            lines=[
                LineOut(
                    product_id=item.product_id,
                    name=item.product_name,
                    colour=item.colour,
                    size=item.size,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    line_total=item.line_total,
                )
                for item in order.items
            ],
            subtotal=order.subtotal,
            shipping=order.shipping,
            total=order.total,
            created_at=order.created_at,
        )


class DeliveryMethodOut(CamelModel):
    id: str
    label: str
    estimate: str
    fee: int
    free_over: int | None


class PaymentMethodOut(CamelModel):
    id: str
    label: str
    note: str


class ProvinceOut(CamelModel):
    name: str
    districts: list[str]


class CheckoutOptionsOut(CamelModel):
    delivery_methods: list[DeliveryMethodOut]
    payment_methods: list[PaymentMethodOut]
    provinces: list[ProvinceOut]
