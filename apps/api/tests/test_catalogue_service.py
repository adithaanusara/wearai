from datetime import date

import pytest

from app.models import Review
from app.services.catalogue import average_rating


def review(rating: int) -> Review:
    return Review(
        id=str(rating),
        style_id="s",
        rating=rating,
        title="",
        body="",
        author="",
        review_date=date(2026, 1, 1),
    )


@pytest.mark.parametrize(
    ("ratings", "expected"),
    [
        ([], None),
        ([5], 5.0),
        ([5, 4, 4], 4.3),
        ([5, 4], 4.5),
        # Rounds half up like the website does, not to the nearest even number.
        ([5, 5, 5, 4, 4, 4, 4, 4, 4, 4], 4.3),
        ([1, 2], 1.5),
    ],
)
def test_average_rating_rounds_half_up_to_one_decimal(ratings: list[int], expected) -> None:
    assert average_rating([review(r) for r in ratings]) == expected
