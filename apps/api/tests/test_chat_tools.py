import json

import pytest
from sqlalchemy.orm import Session

from app.models import Product
from app.services import catalogue
from app.services.chat_tools import MAX_RESULTS, TOOL_NAMES, TOOLS, execute_tool

pytestmark = pytest.mark.usefixtures("catalogue")


def run(db: Session, name: str, arguments, seen: dict | None = None):
    seen = {} if seen is None else seen
    return execute_tool(db, name, arguments, seen), seen


def ids(result) -> list[str]:
    return [p["id"] for p in json.loads(result.content)["products"]]


def test_the_assistant_has_only_these_read_only_tools() -> None:
    assert TOOL_NAMES == {"search_products", "get_product", "get_store_info"}
    described = json.dumps(TOOLS).lower()
    # Nothing that could reach orders, accounts or personal data, or change anything.
    for word in ("order", "email", "password", "address", "payment_method", "cart", "delete"):
        assert word not in json.dumps([t["input_schema"] for t in TOOLS]).lower(), word
    assert "checkout" not in described


def test_search_finds_products_by_keyword(db: Session) -> None:
    result, seen = run(db, "search_products", {"query": "hoodie"})

    assert not result.is_error
    assert set(ids(result)) == {"w-hood-01", "m-hood-01", "m-hood-02"}
    assert set(seen) == {"w-hood-01", "m-hood-01", "m-hood-02"}


def test_search_filters_combine(db: Session) -> None:
    result, _ = run(
        db, "search_products", {"gender": "men", "category": "hoodies", "max_price": 9450}
    )

    assert ids(result) == ["m-hood-01", "m-hood-02"]


def test_unisex_products_count_for_both_genders(db: Session) -> None:
    women, _ = run(db, "search_products", {"gender": "women", "category": "bags"})
    men, _ = run(db, "search_products", {"gender": "men", "category": "bags"})

    assert ids(women) == ids(men) == ["a-bag-01"]


def test_price_sale_and_new_filters(db: Session) -> None:
    cheap, _ = run(db, "search_products", {"max_price": 3000})
    sale, _ = run(db, "search_products", {"on_sale": True})
    new, _ = run(db, "search_products", {"new_only": True})

    assert set(ids(cheap)) == {"a-cap-01", "a-sock-01", "a-bottle-01"}
    assert set(ids(sale)) == {"w-short-01", "m-short-01", "a-cap-01"}
    assert json.loads(new.content)["total_matches"] == 9


def test_browsing_is_limited_and_reports_the_total(db: Session) -> None:
    result, seen = run(db, "search_products", {})

    body = json.loads(result.content)
    assert body["total_matches"] == 17 and len(body["products"]) == MAX_RESULTS
    assert len(seen) == MAX_RESULTS  # only what was shown can become a product card


def test_nothing_found_gives_a_hint_not_an_error(db: Session) -> None:
    result, seen = run(db, "search_products", {"query": "zzzz"})

    body = json.loads(result.content)
    assert not result.is_error and body["products"] == [] and "hint" in body
    assert seen == {}


def test_products_show_exact_prices_and_offered_sizes_but_no_stock(db: Session) -> None:
    result, _ = run(db, "search_products", {"query": "training shorts"})

    shorts = json.loads(result.content)["products"][0]
    assert shorts["price"] == "LKR 3,950.00" and shorts["original_price"] == "LKR 4,950.00"
    assert shorts["sizes_offered"] == ["XS", "S", "M", "L"]
    assert not any("stock" in key for key in shorts)


def test_get_product_by_id_or_slug_with_other_colours(db: Session) -> None:
    by_id, seen = run(db, "get_product", {"product": "m-hood-01"})
    by_slug, _ = run(db, "get_product", {"product": "pullover-hoodie"})

    body = json.loads(by_id.content)
    assert json.loads(by_slug.content)["id"] == body["id"] == "m-hood-01"
    assert body["other_colours"] == [
        {"id": "m-hood-02", "slug": "pullover-hoodie-black", "colour": "Black"}
    ]
    assert body["description"] and body["details"]
    assert set(seen) == {
        "m-hood-01",
        "m-hood-02",
    }  # the other colour was returned, so it may be shown


def test_an_unknown_product_is_an_error_result(db: Session) -> None:
    result, seen = run(db, "get_product", {"product": "nope"})

    assert result.is_error and seen == {}


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("search_products", {"query": "x" * 101}),
        ("search_products", {"gender": "kids"}),
        ("search_products", {"category": "spaceships"}),
        ("search_products", {"max_price": -5}),
        ("search_products", {"max_price": "cheap"}),
        ("search_products", {"unexpected": 1}),
        ("search_products", "not an object"),
        ("get_product", {}),
        ("get_product", {"product": ""}),
        ("get_store_info", {"topic": "secrets"}),
        ("get_store_info", {}),
        ("get_store_info", None),
    ],
)
def test_invalid_arguments_become_error_results_without_echoing_them(
    db: Session, name: str, arguments
) -> None:
    result, _ = run(db, name, arguments)

    assert result.is_error
    assert "Invalid arguments" in result.content
    assert "spaceships" not in result.content and "cheap" not in result.content


def test_an_unknown_tool_is_an_error(db: Session) -> None:
    result, _ = run(db, "delete_everything", {})

    assert result.is_error and "Unknown tool" in result.content


def test_a_failing_tool_does_not_break_the_chat(
    db: Session, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("database exploded: secret detail")

    monkeypatch.setattr(catalogue, "search_products", boom)

    result, _ = run(db, "search_products", {"query": "hoodie"})

    assert result.is_error and "temporarily unavailable" in result.content
    assert "secret detail" not in result.content


def test_store_info_returns_real_facts(db: Session) -> None:
    result, _ = run(db, "get_store_info", {"topic": "delivery"})

    assert "LKR 450.00" in result.content and "LKR 15,000.00" in result.content


def test_the_products_a_tool_returned_are_real_rows(db: Session) -> None:
    _, seen = run(db, "search_products", {"query": "leggings"})

    assert seen and all(isinstance(p, Product) and db.get(Product, p.id) for p in seen.values())
