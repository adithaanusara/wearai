import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Product, ProductImage, Review
from app.seed import CATALOGUE_PATH, load_catalogue


def test_seed_loads_the_whole_catalogue(db: Session) -> None:
    expected = json.loads(CATALOGUE_PATH.read_text())

    products, reviews = load_catalogue(db)

    assert (products, reviews) == (len(expected["products"]), len(expected["reviews"]))
    assert db.scalar(select(func.count()).select_from(Product)) == products
    assert db.scalar(select(func.count()).select_from(Review)) == reviews


def test_seed_can_run_twice_without_duplicating_rows(db: Session) -> None:
    load_catalogue(db)
    counts = [
        db.scalar(select(func.count()).select_from(Product)),
        db.scalar(select(func.count()).select_from(ProductImage)),
    ]

    load_catalogue(db)

    assert [
        db.scalar(select(func.count()).select_from(Product)),
        db.scalar(select(func.count()).select_from(ProductImage)),
    ] == counts


def test_seeded_product_has_its_details(db: Session) -> None:
    load_catalogue(db)

    hoodie = db.scalars(select(Product).where(Product.slug == "pullover-hoodie")).one()

    assert hoodie.colour == "Dark Grey"
    assert hoodie.style_id == "pullover-hoodie"
    assert [size.label for size in hoodie.sizes] == ["M", "L", "XL"]
    assert len(hoodie.images) == 2
    assert hoodie.price == 9450


def test_seed_keeps_sale_prices_and_colourways(db: Session) -> None:
    load_catalogue(db)

    on_sale = db.scalars(select(Product).where(Product.compare_at_price.is_not(None))).all()
    hoodies = db.scalars(select(Product).where(Product.style_id == "pullover-hoodie")).all()

    assert len(on_sale) == 3
    assert all(product.compare_at_price > product.price for product in on_sale)
    assert sorted(product.colour for product in hoodies) == ["Black", "Dark Grey"]
