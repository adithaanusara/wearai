"""The chat assistant's tools. All of them only read the store's own data.

There are deliberately no tools for orders, accounts or writing anything, so even a successful
prompt injection cannot make the assistant reach personal data or change anything.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.formatting import format_lkr
from app.models import Product
from app.schemas_orders import MAX_MONEY
from app.services import catalogue
from app.store_info import TOPICS, store_info

logger = logging.getLogger(__name__)

MAX_RESULTS = 6
_CATEGORIES = [
    "t-shirts",
    "leggings",
    "hoodies",
    "shorts",
    "joggers",
    "bags",
    "caps",
    "socks",
    "bottles",
]

TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_products",
        "description": (
            "Search the store's products. Pass a few short keywords (a product type or a colour, "
            "for example 'black hoodie') as `query`, not a whole sentence, and use the filters for "
            "the rest. Returns up to 6 matching products with their prices and offered sizes. "
            "Leave every field empty to browse."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A few keywords, or empty."},
                "gender": {"type": "string", "enum": ["women", "men", "unisex"]},
                "category": {"type": "string", "enum": _CATEGORIES},
                "max_price": {"type": "integer", "description": "Highest price in LKR."},
                "on_sale": {"type": "boolean", "description": "Only items with a reduced price."},
                "new_only": {"type": "boolean", "description": "Only new arrivals."},
            },
        },
    },
    {
        "name": "get_product",
        "description": (
            "Get the full details of one product: description, colours, sizes offered and price. "
            "Pass its id or slug from a search result."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"product": {"type": "string", "description": "Product id or slug."}},
            "required": ["product"],
        },
    },
    {
        "name": "get_store_info",
        "description": (
            "Get the store's own information about delivery fees and times, payment methods, "
            "sizing, returns and exchanges, or how to contact the store."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "enum": list(TOPICS)}},
            "required": ["topic"],
        },
    },
]

TOOL_NAMES = frozenset(tool["name"] for tool in TOOLS)


class SearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(default="", max_length=100)
    gender: Literal["women", "men", "unisex"] | None = None
    category: (
        Literal[
            "t-shirts",
            "leggings",
            "hoodies",
            "shorts",
            "joggers",
            "bags",
            "caps",
            "socks",
            "bottles",
        ]
        | None
    ) = None
    max_price: int | None = Field(default=None, ge=0, le=MAX_MONEY)
    on_sale: bool | None = None
    new_only: bool | None = None


class GetProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str = Field(min_length=1, max_length=100)


class StoreInfoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Literal["delivery", "payment", "sizing", "returns", "contact"]


@dataclass(frozen=True)
class ToolResult:
    content: str
    is_error: bool = False


def _card(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "colour": product.colour,
        "gender": product.gender,
        "category": product.category,
        "price": format_lkr(product.price),
        "original_price": (
            format_lkr(product.compare_at_price) if product.compare_at_price is not None else None
        ),
        "new_arrival": product.is_new,
        # The store does not track stock, so these are the sizes it offers, not what is in stock.
        "sizes_offered": [size.label for size in product.sizes],
    }


def _search(db: Session, args: SearchInput, seen: dict[str, Product]) -> str:
    if args.query.strip():
        candidates = catalogue.search_products(db, args.query)
    else:
        candidates = list(
            db.scalars(
                select(Product)
                .options(
                    selectinload(Product.sizes),
                    selectinload(Product.images),
                    selectinload(Product.details),
                )
                .order_by(Product.position, Product.id)
            )
        )

    matches = [
        product
        for product in candidates
        # Unisex products, such as accessories, count for both women and men.
        if (args.gender is None or product.gender in (args.gender, "unisex"))
        and (args.category is None or product.category == args.category)
        and (args.max_price is None or product.price <= args.max_price)
        and (not args.on_sale or product.compare_at_price is not None)
        and (not args.new_only or product.is_new)
    ]
    shown = matches[:MAX_RESULTS]
    for product in shown:
        seen[product.id] = product

    result: dict[str, Any] = {
        "total_matches": len(matches),
        "products": [_card(product) for product in shown],
    }
    if not shown:
        result["hint"] = "Nothing matched. Try fewer or different keywords, or fewer filters."
    return json.dumps(result)


def _get_product(db: Session, args: GetProductInput, seen: dict[str, Product]) -> ToolResult:
    product = db.get(Product, args.product) or catalogue.get_product(db, args.product)
    if product is None:
        return ToolResult("No product with that id or slug.", is_error=True)

    seen[product.id] = product
    colours = []
    for other in catalogue.get_colourways(db, product):
        if other.id != product.id:
            seen[other.id] = other
            colours.append({"id": other.id, "slug": other.slug, "colour": other.colour})

    return ToolResult(
        json.dumps(
            {
                **_card(product),
                "description": product.description,
                "details": [detail.text for detail in product.details],
                "other_colours": colours,
            }
        )
    )


def execute_tool(db: Session, name: str, raw_input: Any, seen: dict[str, Product]) -> ToolResult:
    """Runs one tool. `seen` collects the products it returns, so answers can only show those."""
    if name not in TOOL_NAMES:
        return ToolResult(f"Unknown tool: {name}", is_error=True)

    try:
        match name:
            case "search_products":
                return ToolResult(_search(db, SearchInput.model_validate(raw_input), seen))
            case "get_product":
                return _get_product(db, GetProductInput.model_validate(raw_input), seen)
            case _:
                info = store_info(StoreInfoInput.model_validate(raw_input).topic)
                return ToolResult(json.dumps(info))
    except ValidationError:
        # Not echoed back: the model only needs to know the arguments were wrong.
        return ToolResult(
            "Invalid arguments for this tool. Check the tool description.", is_error=True
        )
    except Exception:  # a tool failing must never take the whole chat down
        logger.exception("chat tool failed: %s", name)
        return ToolResult("This tool is temporarily unavailable.", is_error=True)
