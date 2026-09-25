import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

pytestmark = pytest.mark.usefixtures("catalogue")

# The starter catalogue in featured order, by product id.
FEATURED = [
    "w-tee-01", "w-tee-02", "w-leg-01", "w-leg-03", "w-hood-01", "w-short-01", "w-leg-02",
    "m-tee-01", "m-short-01", "m-hood-01", "m-hood-02", "m-jog-01", "m-tee-02",
    "a-bag-01", "a-cap-01", "a-sock-01", "a-bottle-01",
]  # fmt: skip


def ids(response) -> list[str]:
    return [item["id"] for item in response.json()["items"]]


def test_lists_the_catalogue_in_featured_order(client: TestClient) -> None:
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert ids(response) == FEATURED
    body = response.json()
    assert (body["total"], body["page"], body["pageSize"]) == (17, 1, 24)


def test_json_uses_camel_case_matching_the_web_types(client: TestClient) -> None:
    product = client.get("/api/v1/products").json()["items"][0]

    assert {"styleId", "compareAtPrice", "isNew", "isBestSeller"} <= product.keys()
    assert "style_id" not in product
    assert product["images"] == ["/images/placeholder.svg", "/images/placeholder-alt.svg"]
    assert product["sizes"] == ["XS", "S", "M", "L"]


def test_pagination_returns_the_requested_slice(client: TestClient) -> None:
    second = client.get("/api/v1/products?pageSize=5&page=2")
    last = client.get("/api/v1/products?pageSize=5&page=4")
    beyond = client.get("/api/v1/products?pageSize=5&page=9")

    assert ids(second) == FEATURED[5:10]
    assert second.json()["total"] == 17
    assert ids(last) == FEATURED[15:]
    assert ids(beyond) == []


@pytest.mark.parametrize("query", ["page=0", "pageSize=0", "pageSize=101", "page=abc"])
def test_invalid_pagination_is_rejected(client: TestClient, query: str) -> None:
    assert client.get(f"/api/v1/products?{query}").status_code == 422


def test_filters_by_gender_and_category(client: TestClient) -> None:
    assert ids(client.get("/api/v1/products?gender=women")) == FEATURED[:7]
    assert client.get("/api/v1/products?gender=unisex").json()["total"] == 4
    assert ids(client.get("/api/v1/products?category=hoodies")) == [
        "w-hood-01",
        "m-hood-01",
        "m-hood-02",
    ]


def test_size_filter_matches_any_selected_size(client: TestClient) -> None:
    only_xl = client.get("/api/v1/products?size=XL")
    xs_or_xl = client.get("/api/v1/products?size=XS&size=XL")

    assert only_xl.json()["total"] == 9
    assert {"w-tee-01", "w-leg-01"} <= set(ids(xs_or_xl))
    assert "w-hood-01" not in ids(xs_or_xl)  # sizes S, M, L only


def test_colour_and_price_filters_combine(client: TestClient) -> None:
    both_colours = client.get("/api/v1/products?colour=White&colour=Stone")
    priced = client.get("/api/v1/products?min=3250&max=3650")
    combined = client.get("/api/v1/products?colour=Black&min=3000&max=4000")

    assert {p["colour"] for p in both_colours.json()["items"]} == {"White", "Stone"}
    # Both price limits are inclusive.
    assert ids(priced) == ["w-tee-01", "w-tee-02", "m-tee-01", "m-tee-02"]
    assert ids(combined) == ["w-tee-01", "w-short-01", "m-tee-02"]


def test_sorting(client: TestClient) -> None:
    cheapest = client.get("/api/v1/products?sort=price-asc").json()["items"]
    dearest = client.get("/api/v1/products?sort=price-desc").json()["items"]
    newest = client.get("/api/v1/products?sort=newest").json()["items"]

    assert [p["price"] for p in cheapest] == sorted(p["price"] for p in cheapest)
    assert cheapest[0]["id"] == "a-sock-01"
    assert [p["price"] for p in dearest] == sorted((p["price"] for p in dearest), reverse=True)
    # Equal prices keep the featured order.
    assert [p["id"] for p in dearest][:3] == ["m-hood-01", "m-hood-02", "w-hood-01"]
    flags = [p["isNew"] for p in newest]
    assert flags == sorted(flags, reverse=True)
    # Within each group the featured order is kept.
    new_ids = [p["id"] for p in newest if p["isNew"]]
    assert new_ids == [i for i in FEATURED if i in new_ids]


@pytest.mark.parametrize(
    "query",
    ["sort=bogus", "min=-1", "max=abc", "min=5000&max=4000", "gender=kids"],
)
def test_invalid_filters_are_rejected_not_ignored(client: TestClient, query: str) -> None:
    assert client.get(f"/api/v1/products?{query}").status_code == 422


def test_listing_uses_a_fixed_number_of_queries(client: TestClient, db: Session) -> None:
    statements: list[str] = []
    event.listen(db.get_bind(), "before_cursor_execute", lambda *args: statements.append(args[2]))

    response = client.get("/api/v1/products?pageSize=17")

    assert response.json()["total"] == 17
    # A count, the page, and one query each for images, sizes and details, not one per product.
    assert len(statements) <= 6


def test_product_detail_includes_colourways_and_rating(client: TestClient) -> None:
    response = client.get("/api/v1/products/pullover-hoodie")

    body = response.json()
    assert response.status_code == 200
    assert body["colour"] == "Dark Grey"
    assert [(c["slug"], c["colour"]) for c in body["colourways"]] == [
        ("pullover-hoodie", "Dark Grey"),
        ("pullover-hoodie-black", "Black"),
    ]
    assert body["rating"] == {"average": 5.0, "count": 1}


def test_rating_is_shared_by_every_colour_and_rounded(client: TestClient) -> None:
    black = client.get("/api/v1/products/essential-fitted-tee").json()
    white = client.get("/api/v1/products/essential-fitted-tee-white").json()

    assert black["rating"] == white["rating"] == {"average": 4.5, "count": 2}


def test_product_without_reviews_has_no_average(client: TestClient) -> None:
    body = client.get("/api/v1/products/everyday-cap").json()

    assert body["rating"] == {"average": None, "count": 0}
    assert body["compareAtPrice"] == 3250


def test_unknown_or_oversized_slug(client: TestClient) -> None:
    missing = client.get("/api/v1/products/nope")

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Product not found"}
    assert client.get(f"/api/v1/products/{'a' * 101}").status_code == 422


def test_reviews_for_a_style(client: TestClient) -> None:
    reviews = client.get("/api/v1/products/essential-fitted-tee-white/reviews").json()

    assert [r["id"] for r in reviews] == ["r1", "r2"]
    assert reviews[0]["date"] == "2026-08-14"
    assert reviews[0]["styleId"] == "essential-fitted-tee"
    assert client.get("/api/v1/products/everyday-cap/reviews").json() == []
    assert client.get("/api/v1/products/nope/reviews").status_code == 404


def test_related_products_share_a_category_but_not_a_style(client: TestClient) -> None:
    related = client.get("/api/v1/products/seamless-high-rise-leggings/related").json()

    assert [p["slug"] for p in related] == ["ribbed-studio-leggings"]
    assert (
        client.get("/api/v1/products/seamless-high-rise-leggings/related?limit=13").status_code
        == 422
    )
    assert client.get("/api/v1/products/nope/related").status_code == 404
