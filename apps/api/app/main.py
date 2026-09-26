from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, auth, chat, checkout, collections, health, orders, products, search
from app.config import settings

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
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(checkout.router, prefix=API_PREFIX)
    app.include_router(orders.router, prefix=API_PREFIX)
    app.include_router(chat.router, prefix=API_PREFIX)
    app.include_router(admin.router, prefix=API_PREFIX)
    app.include_router(products.router, prefix=API_PREFIX)
    app.include_router(collections.router, prefix=API_PREFIX)
    app.include_router(search.router, prefix=API_PREFIX)
    return app


app = create_app()
