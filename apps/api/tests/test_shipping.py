import pytest

from app.checkout_data import PROVINCES, calculate_shipping


@pytest.mark.parametrize(
    ("subtotal", "method", "expected"),
    [
        (5000, "standard", 450),
        (14999, "standard", 450),
        (15000, "standard", 0),  # free from the threshold itself
        (40000, "standard", 0),
        (40000, "express", 950),  # express is never free
        (1000, "pickup", 0),
        (1000, "drone", 0),  # unknown methods cost nothing, as on the website
        (0, "standard", 450),
    ],
)
def test_shipping_fees(subtotal: int, method: str, expected: int) -> None:
    assert calculate_shipping(subtotal, method) == expected


def test_sri_lanka_has_nine_provinces_and_twenty_five_districts() -> None:
    assert len(PROVINCES) == 9
    districts = [district for group in PROVINCES.values() for district in group]
    assert len(districts) == 25
    assert len(set(districts)) == 25
