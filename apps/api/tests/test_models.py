from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product, ProductImage, ProductSize, Review, User


def make_product(**overrides) -> Product:
    values = {
        "id": "t-01",
        "slug": "test-tee",
        "style_id": "test-tee",
        "name": "Test Tee",
        "gender": "women",
        "category": "t-shirts",
        "colour": "Black",
        "price": 3000,
        "description": "A tee.",
    }
    return Product(**{**values, **overrides})


def test_product_keeps_images_and_sizes_in_position_order(db: Session) -> None:
    product = make_product(
        images=[ProductImage(url="/b.svg", position=1), ProductImage(url="/a.svg", position=0)],
        sizes=[ProductSize(label="L", position=1), ProductSize(label="S", position=0)],
    )
    db.add(product)
    db.commit()
    db.expire_all()

    saved = db.get(Product, "t-01")
    assert [image.url for image in saved.images] == ["/a.svg", "/b.svg"]
    assert [size.label for size in saved.sizes] == ["S", "L"]
    assert saved.is_new is False
    assert saved.compare_at_price is None


def test_deleting_a_product_removes_its_images(db: Session) -> None:
    db.add(make_product(images=[ProductImage(url="/a.svg", position=0)]))
    db.commit()

    db.delete(db.get(Product, "t-01"))
    db.commit()

    assert db.scalars(select(ProductImage)).all() == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"price": -1},
        {"gender": "kids"},
        {"price": 3000, "compare_at_price": 3000},
        {"price": 3000, "compare_at_price": 2000},
    ],
    ids=["negative price", "unknown gender", "compare price equal", "compare price lower"],
)
def test_product_constraints_reject_bad_data(db: Session, overrides: dict) -> None:
    db.add(make_product(**overrides))

    with pytest.raises(IntegrityError):
        db.flush()


def test_product_slug_must_be_unique(db: Session) -> None:
    db.add(make_product())
    db.flush()
    db.add(make_product(id="t-02"))

    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize("rating", [0, 6])
def test_review_rating_must_be_between_one_and_five(db: Session, rating: int) -> None:
    db.add(
        Review(
            id="r-1",
            style_id="test-tee",
            rating=rating,
            title="T",
            body="B",
            author="A",
            review_date=date(2026, 1, 1),
        )
    )

    with pytest.raises(IntegrityError):
        db.flush()


def test_user_email_must_be_unique(db: Session) -> None:
    db.add(User(email="a@example.com", name="A", password_hash="x"))
    db.flush()
    db.add(User(email="a@example.com", name="B", password_hash="y"))

    with pytest.raises(IntegrityError):
        db.flush()


def test_user_gets_a_creation_time(db: Session) -> None:
    user = User(email="a@example.com", name="A", password_hash="x")
    db.add(user)
    db.commit()

    assert user.created_at is not None
