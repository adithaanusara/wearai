"""Facts the chat assistant may quote about the store. It answers from here, never from memory.

The delivery and payment facts come from the same data the checkout uses, so the two cannot
disagree. The returns terms and contact details below are PLACEHOLDERS, matching the website; they
must be replaced with the real ones before launch.
"""

from typing import Literal

from app.checkout_data import DELIVERY_METHODS, PAYMENT_METHODS
from app.formatting import format_lkr

Topic = Literal["delivery", "payment", "sizing", "returns", "contact"]
TOPICS: tuple[str, ...] = ("delivery", "payment", "sizing", "returns", "contact")

# Body measurements in centimetres, as on the product pages' size guide.
SIZE_CHART = [
    {"size": "XS", "chest": 80, "waist": 62, "hip": 88},
    {"size": "S", "chest": 86, "waist": 68, "hip": 94},
    {"size": "M", "chest": 92, "waist": 74, "hip": 100},
    {"size": "L", "chest": 98, "waist": 80, "hip": 106},
    {"size": "XL", "chest": 104, "waist": 86, "hip": 112},
]

# PLACEHOLDER values: replace before launch.
CONTACT = {
    "email": "support@example.com",
    "phone": "+94 11 000 0000",
    "hours": "Monday to Friday, 9:00 to 17:00",
}
RETURN_WINDOW_DAYS = 14


def store_info(topic: Topic) -> dict:
    match topic:
        case "delivery":
            return {
                "methods": [
                    {
                        "name": method.label,
                        "fee": "free" if method.fee == 0 else format_lkr(method.fee),
                        "free_when_order_is_at_least": (
                            format_lkr(method.free_over) if method.free_over is not None else None
                        ),
                        "estimated_time": method.estimate,
                    }
                    for method in DELIVERY_METHODS.values()
                ],
                "note": "The delivery fee is shown at checkout before the order is placed.",
            }
        case "payment":
            return {
                "methods": [{"name": m.label, "details": m.note} for m in PAYMENT_METHODS.values()]
            }
        case "sizing":
            return {
                "measurements_cm": SIZE_CHART,
                "advice": "Every product page has a size guide. If you are between sizes, "
                "choose the larger one for a relaxed fit.",
            }
        case "returns":
            return {
                "return_window_days": RETURN_WINDOW_DAYS,
                "conditions": "Items must be unworn, unwashed and in original condition, with "
                "tags and packaging.",
                "how_to_start": f"Email {CONTACT['email']} with the order reference and say "
                "whether you want a refund or an exchange.",
                "exchanges": "Exchanges are subject to stock.",
            }
        case "contact":
            return CONTACT
