from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    admin,
    auth,
    chat,
    checkout,
    collections,
    health,
    media,
    orders,
    products,
    search,
)
from app.config import settings
from app.services.images import MAX_BYTES

API_PREFIX = "/api/v1"


def _friendly_message(item: dict) -> str:
    """Turns the library's technical wording into something a shopper can act on."""
    message = item["msg"].removeprefix("Value error, ")
    if item["type"] == "missing":
        return "This field is required."
    if item["type"] == "string_too_short" and item.get("ctx", {}).get("min_length") == 1:
        return "This field is required."
    if message.startswith("value is not a valid email address"):
        return "Enter a valid email address."
    return message


def _validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    """A 422 that says what is wrong but never echoes the submitted values, such as passwords."""
    problems = [
        {"loc": item["loc"], "msg": _friendly_message(item), "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": problems})


# The image plus a little room for the multipart wrapping around it.
UPLOAD_BODY_LIMIT = MAX_BYTES + 64 * 1024


async def _limit_upload_size(request: Request, call_next):
    """Turns away an oversized image upload from its headers, before the body is read.

    The upload parser would otherwise accept the whole body first. A request that does not say
    how big it is (chunked) is refused too, so the limit cannot be skipped.
    """
    path = request.url.path
    if request.method == "POST" and path.startswith(f"{API_PREFIX}/admin/products/"):
        if path.endswith("/images"):
            length = request.headers.get("content-length", "")
            if not length.isdigit():
                return JSONResponse(
                    status_code=411,
                    content={"detail": {"code": "length_required", "message": "Length required."}},
                )
            if int(length) > UPLOAD_BODY_LIMIT:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": {
                            "code": "image_too_large",
                            "message": "The image is too large (at most 5 MB).",
                        }
                    },
                )
    return await call_next(request)


def create_app() -> FastAPI:
    app = FastAPI(title="Store API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.middleware("http")(_limit_upload_size)
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(checkout.router, prefix=API_PREFIX)
    app.include_router(orders.router, prefix=API_PREFIX)
    app.include_router(chat.router, prefix=API_PREFIX)
    app.include_router(admin.router, prefix=API_PREFIX)
    app.include_router(media.router, prefix=API_PREFIX)
    app.include_router(products.router, prefix=API_PREFIX)
    app.include_router(collections.router, prefix=API_PREFIX)
    app.include_router(search.router, prefix=API_PREFIX)
    return app


app = create_app()
