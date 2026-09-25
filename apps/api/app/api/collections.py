from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api.deps import FiltersDep, PaginationDep
from app.db import get_db
from app.schemas import CollectionOut, FilterOptionsOut, ProductOut
from app.services import catalogue
from app.services.collections import get_collection

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/{slug}", response_model=CollectionOut)
def get_collection_products(
    slug: Annotated[str, Path(max_length=100)],
    db: Annotated[Session, Depends(get_db)],
    filters: FiltersDep,
    pagination: PaginationDep,
) -> CollectionOut:
    collection = get_collection(slug)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    products, total = catalogue.list_products(
        db,
        filters,
        page=pagination.page,
        page_size=pagination.page_size,
        scope=collection.condition,
    )
    return CollectionOut(
        slug=collection.slug,
        title=collection.title,
        # Options come from the whole collection, so choices stay when filters are applied.
        filter_options=FilterOptionsOut(**catalogue.filter_options(db, collection.condition)),
        items=[ProductOut.from_product(product) for product in products],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
