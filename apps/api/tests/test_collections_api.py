import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("catalogue")


def ids(response) -> list[str]:
    return [item["id"] for item in response.json()["items"]]


def test_gender_collection_includes_unisex_products(client: TestClient) -> None:
    response = client.get("/api/v1/collections/women")

    body = response.json()
    assert response.status_code == 200
    assert (body["slug"], body["title"], body["total"]) == ("women", "Women", 11)
    genders = {item["gender"] for item in body["items"]}
    assert genders == {"women", "unisex"}


def test_category_collections(client: TestClient) -> None:
    leggings = client.get("/api/v1/collections/women-leggings")

    assert leggings.json()["title"] == "Women Leggings"
    assert ids(leggings) == ["w-leg-01", "w-leg-03", "w-leg-02"]
    assert ids(client.get("/api/v1/collections/bags")) == ["a-bag-01"]


def test_new_best_seller_and_last_chance_collections(client: TestClient) -> None:
    assert client.get("/api/v1/collections/new").json()["total"] == 9
    assert ids(client.get("/api/v1/collections/men-best-sellers")) == [
        "m-tee-01",
        "m-jog-01",
        "a-bag-01",
    ]
    last_chance = client.get("/api/v1/collections/last-chance")
    assert ids(last_chance) == ["w-short-01", "m-short-01", "a-cap-01"]
    assert all(item["compareAtPrice"] > item["price"] for item in last_chance.json()["items"])


def test_filters_apply_inside_a_collection(client: TestClient) -> None:
    response = client.get("/api/v1/collections/women-leggings?colour=Black&sort=price-desc")

    assert ids(response) == ["w-leg-03"]
    assert response.json()["total"] == 1


def test_filter_options_describe_the_whole_collection(client: TestClient) -> None:
    unfiltered = client.get("/api/v1/collections/women-leggings").json()["filterOptions"]
    filtered = client.get("/api/v1/collections/women-leggings?colour=Black").json()["filterOptions"]

    assert unfiltered == {
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colours": ["Black", "Charcoal", "Stone"],
        "minPrice": 5950,
        "maxPrice": 6450,
    }
    # Choosing a colour does not remove the other choices.
    assert filtered == unfiltered


def test_collection_pagination(client: TestClient) -> None:
    response = client.get("/api/v1/collections/women?pageSize=4&page=3")

    assert response.json()["total"] == 11
    assert len(response.json()["items"]) == 3


def test_unknown_collection_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/collections/nope")

    assert response.status_code == 404
    assert response.json() == {"detail": "Collection not found"}


def test_collection_rejects_invalid_filters(client: TestClient) -> None:
    assert client.get("/api/v1/collections/women?sort=bogus").status_code == 422
    assert client.get("/api/v1/collections/women?min=9&max=1").status_code == 422
