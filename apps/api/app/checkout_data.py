"""Delivery, payment and location data for checkout. It mirrors what the website shows today."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeliveryMethod:
    id: str
    label: str
    estimate: str
    fee: int  # whole LKR
    free_over: int | None = None  # a subtotal at or above this ships free


@dataclass(frozen=True)
class PaymentMethod:
    id: str
    label: str
    note: str


DELIVERY_METHODS: dict[str, DeliveryMethod] = {
    method.id: method
    for method in [
        DeliveryMethod("standard", "Standard delivery", "3–5 business days", 450, free_over=15000),
        DeliveryMethod("express", "Express delivery", "1–2 business days", 950),
        DeliveryMethod("pickup", "Store pickup", "Ready in 1 business day", 0),
    ]
}

PAYMENT_METHODS: dict[str, PaymentMethod] = {
    method.id: method
    for method in [
        PaymentMethod("cod", "Cash on delivery", "Pay in cash when your order arrives."),
        PaymentMethod(
            "bank-transfer",
            "Bank transfer",
            "We will email our bank details. Your order ships once the payment is received.",
        ),
        PaymentMethod(
            "card",
            "Credit or debit card",
            "You will be taken to a secure payment page after placing the order.",
        ),
    ]
}

PROVINCES: dict[str, list[str]] = {
    "Central": ["Kandy", "Matale", "Nuwara Eliya"],
    "Eastern": ["Ampara", "Batticaloa", "Trincomalee"],
    "North Central": ["Anuradhapura", "Polonnaruwa"],
    "North Western": ["Kurunegala", "Puttalam"],
    "Northern": ["Jaffna", "Kilinochchi", "Mannar", "Mullaitivu", "Vavuniya"],
    "Sabaragamuwa": ["Kegalle", "Ratnapura"],
    "Southern": ["Galle", "Hambantota", "Matara"],
    "Uva": ["Badulla", "Monaragala"],
    "Western": ["Colombo", "Gampaha", "Kalutara"],
}


def calculate_shipping(subtotal: int, method_id: str) -> int:
    """Shipping in whole LKR. An unknown method costs nothing, as on the website."""
    method = DELIVERY_METHODS.get(method_id)
    if method is None:
        return 0
    if method.free_over is not None and subtotal >= method.free_over:
        return 0
    return method.fee
