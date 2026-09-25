"""Product queries: filtering, sorting, search ranking, related products and ratings."""

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, ProductSize, Review

MAX_QUERY_LENGTH = 100
_SIZE_ORDER = ["XS", "S", "M", "L", "XL", "One Size"]


class SortKey(StrEnum):
    FEATURED = "featured"
    NEWEST = "newest"
    PRICE_ASC = "price-asc"
    PRICE_DESC = "price-desc"


@dataclass
class Filters:
    sizes: list[str] = field(default_factory=list)
    colours: list[str] = field(default_factory=list)
    min_price: int | None = None
    max_price: int | None = None
    gender: str | None = None
    category: str | None = None
    ids: list[str] = field(default_factory=list)
    sort: SortKey = SortKey.FEATURED


def _with_children() -> list:
    """Loads images, sizes and details in a few queries instead of one per product."""
    return [
        selectinload(Product.images),
        selectinload(Product.sizes),
        selectinload(Product.details),
    ]


def _conditions(filters: Filters) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if filters.sizes:
        conditions.append(Product.sizes.any(ProductSize.label.in_(filters.sizes)))
    if filters.colours:
        conditions.append(Product.colour.in_(filters.colours))
    if filters.min_price is not None:
        conditions.append(Product.price >= filters.min_price)
    if filters.max_price is not None:
        conditions.append(Product.price <= filters.max_price)
    if filters.gender:
        conditions.append(Product.gender == filters.gender)
    if filters.category:
        conditions.append(Product.category == filters.category)
    if filters.ids:
        conditions.append(Product.id.in_(filters.ids))
    return conditions


def _order_by(sort: SortKey) -> list[ColumnElement]:
    # Position breaks ties, so equal prices keep the featured order.
    match sort:
        case SortKey.NEWEST:
            return [Product.is_new.desc(), Product.position, Product.id]
        case SortKey.PRICE_ASC:
            return [Product.price, Product.position, Product.id]
        case SortKey.PRICE_DESC:
            return [Product.price.desc(), Product.position, Product.id]
        case _:
            return [Product.position, Product.id]


def list_products(
    db: Session,
    filters: Filters,
    *,
    page: int,
    page_size: int,
    scope: ColumnElement[bool] | None = None,
) -> tuple[list[Product], int]:
    """One page of products and the total number that match. `scope` is a collection's rule."""
    conditions = _conditions(filters)
    if scope is not None:
        conditions.append(scope)

    total = db.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0
    query: Select = (
        select(Product)
        .options(*_with_children())
        .where(*conditions)
        .order_by(*_order_by(filters.sort))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(query)), total


def filter_options(db: Session, scope: ColumnElement[bool] | None = None) -> dict:
    """The sizes, colours and price range on offer, based on everything in the scope."""
    query = select(Product).options(selectinload(Product.sizes))
    if scope is not None:
        query = query.where(scope)
    products = list(db.scalars(query))

    sizes = {size.label for product in products for size in product.sizes}
    prices = [product.price for product in products]
    return {
        "sizes": sorted(
            sizes, key=lambda s: _SIZE_ORDER.index(s) if s in _SIZE_ORDER else len(_SIZE_ORDER)
        ),
        "colours": sorted({product.colour for product in products}),
        "min_price": min(prices, default=0),
        "max_price": max(prices, default=0),
    }


def get_product(db: Session, slug: str) -> Product | None:
    return db.scalars(
        select(Product).options(*_with_children()).where(Product.slug == slug)
    ).one_or_none()


def get_colourways(db: Session, product: Product) -> list[Product]:
    """Every colour of the same style, including the product itself, in catalogue order."""
    return list(
        db.scalars(
            select(Product)
            .where(Product.style_id == product.style_id)
            .order_by(Product.position, Product.id)
        )
    )


def get_related(db: Session, product: Product, limit: int) -> list[Product]:
    """Other products in the same category, skipping every colour of the same style."""
    query = (
        select(Product)
        .options(*_with_children())
        .where(Product.category == product.category, Product.style_id != product.style_id)
        .order_by(Product.position, Product.id)
        .limit(limit)
    )
    return list(db.scalars(query))


def get_reviews(db: Session, style_id: str) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .where(Review.style_id == style_id)
            .order_by(Review.review_date, Review.id)
        )
    )


def average_rating(reviews: list[Review]) -> float | None:
    """Average rounded half up to one decimal, or None without reviews."""
    if not reviews:
        return None
    average = sum(review.rating for review in reviews) / len(reviews)
    return math.floor(average * 10 + 0.5) / 10


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def search_products(db: Session, query: str) -> list[Product]:
    """Products where every search word starts a word in the name, colour, category or gender.

    Name matches score 3 and the other fields 1. Matching starts at word boundaries, so "men"
    does not find women's items. Ties keep the featured order.
    """
    terms = _words(query[:MAX_QUERY_LENGTH])
    if not terms:
        return []

    catalogue = db.scalars(
        select(Product).options(*_with_children()).order_by(Product.position, Product.id)
    )
    scored: list[tuple[int, int, Product]] = []
    for index, product in enumerate(catalogue):
        name_words = _words(product.name)
        other_words = _words(f"{product.colour} {product.category} {product.gender}")
        score = 0
        for term in terms:
            if any(word.startswith(term) for word in name_words):
                score += 3
            elif any(word.startswith(term) for word in other_words):
                score += 1
            else:
                break
        else:
            scored.append((score, index, product))

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    return [product for _, _, product in scored]
