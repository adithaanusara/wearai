from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User
from app.services import auth
from app.services.catalogue import Filters, SortKey
from app.services.orders import InvalidCartError

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


def require_trusted_origin(request: Request) -> None:
    """Rejects browser requests that come from a site we do not trust (CSRF defence).

    Browsers always send an Origin header on cross-site POSTs. Requests without one, such as
    curl, cannot be forged from another site, so they are let through.
    """
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise HTTPException(status_code=403, detail="Origin not allowed")


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User | None:
    """The signed-in user from the session cookie, or None."""
    token = request.cookies.get(settings.session_cookie_name)
    return auth.user_for_token(db, token) if token else None


def require_user(user: Annotated[User | None, Depends(current_user)]) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


TrustedOrigin = Depends(require_trusted_origin)
UserDep = Annotated[User, Depends(require_user)]


def cart_problem(error: InvalidCartError) -> HTTPException:
    """A 422 in the same shape as request validation errors, pointing at the offending line."""
    return HTTPException(
        status_code=422,
        detail=[
            {
                "loc": ["body", "items", error.index, error.field],
                "msg": error.message,
                "type": "value_error",
            }
        ],
    )
