from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import PaginationDep
from app.db import get_db
from app.schemas import Page, ProductOut
from app.services import catalogue

router = APIRouter(tags=["search"])


@router.get("/search", response_model=Page[ProductOut])
def search(
    db: Annotated[Session, Depends(get_db)],
    pagination: PaginationDep,
    q: Annotated[str, Query(max_length=catalogue.MAX_QUERY_LENGTH)] = "",
) -> Page[ProductOut]:
    results = catalogue.search_products(db, q)
    start = (pagination.page - 1) * pagination.page_size
    return Page(
        items=[ProductOut.from_product(p) for p in results[start : start + pagination.page_size]],
        total=len(results),
        page=pagination.page,
        page_size=pagination.page_size,
    )
