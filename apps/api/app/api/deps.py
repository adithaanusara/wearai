from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query

from app.services.catalogue import Filters, SortKey

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


@dataclass
class Pagination:
    page: int
    page_size: int


def pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, page_size=page_size)


def filter_params(
    size: Annotated[list[str] | None, Query()] = None,
    colour: Annotated[list[str] | None, Query()] = None,
    min_price: Annotated[int | None, Query(alias="min", ge=0)] = None,
    max_price: Annotated[int | None, Query(alias="max", ge=0)] = None,
    sort: SortKey = SortKey.FEATURED,
) -> Filters:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min must not be greater than max")
    return Filters(
        sizes=size or [],
        colours=colour or [],
        min_price=min_price,
        max_price=max_price,
        sort=sort,
    )


PaginationDep = Annotated[Pagination, Depends(pagination_params)]
FiltersDep = Annotated[Filters, Depends(filter_params)]
