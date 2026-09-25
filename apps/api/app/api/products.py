from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import FiltersDep, PaginationDep
from app.db import get_db
from app.schemas import (
    ColourwayOut,
    Page,
    ProductDetailOut,
    ProductOut,
    RatingOut,
    ReviewOut,
)
from app.services import catalogue

router = APIRouter(prefix="/products", tags=["products"])

DbDep = Annotated[Session, Depends(get_db)]
SlugPath = Annotated[str, Path(max_length=100)]


def _product_or_404(db: Session, slug: str):
    product = catalogue.get_product(db, slug)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=Page[ProductOut])
def list_products(
    db: DbDep,
    filters: FiltersDep,
    pagination: PaginationDep,
    gender: Literal["women", "men", "unisex"] | None = None,
    category: Annotated[str | None, Query(max_length=40)] = None,
) -> Page[ProductOut]:
    filters.gender = gender
    filters.category = category
    products, total = catalogue.list_products(
        db, filters, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[ProductOut.from_product(product) for product in products],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{slug}", response_model=ProductDetailOut)
def get_product(slug: SlugPath, db: DbDep) -> ProductDetailOut:
    product = _product_or_404(db, slug)
    reviews = catalogue.get_reviews(db, product.style_id)
    base = ProductOut.from_product(product)
    return ProductDetailOut(
        **base.model_dump(),
        colourways=[
            ColourwayOut(id=item.id, slug=item.slug, colour=item.colour)
            for item in catalogue.get_colourways(db, product)
        ],
        rating=RatingOut(average=catalogue.average_rating(reviews), count=len(reviews)),
    )


@router.get("/{slug}/reviews", response_model=list[ReviewOut])
def get_reviews(slug: SlugPath, db: DbDep) -> list[ReviewOut]:
    product = _product_or_404(db, slug)
    return [ReviewOut.from_review(review) for review in catalogue.get_reviews(db, product.style_id)]


@router.get("/{slug}/related", response_model=list[ProductOut])
def get_related(
    slug: SlugPath, db: DbDep, limit: Annotated[int, Query(ge=1, le=12)] = 4
) -> list[ProductOut]:
    product = _product_or_404(db, slug)
    return [ProductOut.from_product(item) for item in catalogue.get_related(db, product, limit)]
