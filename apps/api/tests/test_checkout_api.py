import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("catalogue")

QUOTE = "/api/v1/checkout/quote"


def test_options_list_delivery_payment_and_locations(client: TestClient) -> None:
    body = client.get("/api/v1/checkout/options").json()

    assert [m["id"] for m in body["deliveryMethods"]] == ["standard", "express", "pickup"]
    standard = body["deliveryMethods"][0]
    assert (standard["fee"], standard["freeOver"]) == (450, 15000)
    assert body["deliveryMethods"][1]["freeOver"] is None
    assert [m["id"] for m in body["paymentMethods"]] == ["cod", "bank-transfer", "card"]
    assert len(body["provinces"]) == 9
    western = next(p for p in body["provinces"] if p["name"] == "Western")
    assert western["districts"] == ["Colombo", "Gampaha", "Kalutara"]


def test_quote_prices_the_cart_from_the_database(client: TestClient) -> None:
    response = client.post(
        QUOTE,
        json={
            "items": [
                {"productId": "w-tee-01", "size": "M", "quantity": 2},
                {"productId": "m-jog-01", "size": "L", "quantity": 1},
            ],
            "deliveryMethod": "standard",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert [line["lineTotal"] for line in body["lines"]] == [6500, 7450]
    assert (body["subtotal"], body["shipping"], body["total"]) == (13950, 450, 14400)
    assert body["lines"][0]["name"] == "Essential Fitted Tee"


def test_quote_gives_free_standard_shipping_over_the_threshold(client: TestClient) -> None:
    body = client.post(
        QUOTE,
        json={
            "items": [{"productId": "m-hood-01", "size": "L", "quantity": 2}],
            "deliveryMethod": "standard",
        },
    ).json()

    assert (body["subtotal"], body["shipping"], body["total"]) == (18900, 0, 18900)


@pytest.mark.parametrize(("method", "shipping"), [("express", 950), ("pickup", 0)])
def test_quote_other_delivery_methods(client: TestClient, method: str, shipping: int) -> None:
    body = client.post(
        QUOTE,
        json={
            "items": [{"productId": "w-tee-01", "size": "M", "quantity": 1}],
            "deliveryMethod": method,
        },
    ).json()

    assert body["shipping"] == shipping
    assert body["total"] == 3250 + shipping


def test_quote_rejects_bad_carts_and_pointing_at_the_line(client: TestClient) -> None:
    bad_size = client.post(
        QUOTE,
        json={
            "items": [
                {"productId": "w-tee-01", "size": "M", "quantity": 1},
                {"productId": "w-hood-01", "size": "XL", "quantity": 1},  # only S, M, L
            ],
            "deliveryMethod": "standard",
        },
    )
    unknown = client.post(
        QUOTE,
        json={
            "items": [{"productId": "nope", "size": "M", "quantity": 1}],
            "deliveryMethod": "pickup",
        },
    )

    assert bad_size.status_code == 422
    assert bad_size.json()["detail"][0]["loc"] == ["body", "items", 1, "size"]
    assert unknown.status_code == 422
    assert unknown.json()["detail"][0]["loc"] == ["body", "items", 0, "productId"]


@pytest.mark.parametrize(
    "body",
    [
        {"items": [], "deliveryMethod": "standard"},
        {
            "items": [{"productId": "w-tee-01", "size": "M", "quantity": 1}],
            "deliveryMethod": "drone",
        },
        {"items": [{"productId": "w-tee-01", "size": "M", "quantity": 1}]},
        {
            "items": [{"productId": "w-tee-01", "size": "M", "quantity": 1, "price": 1}],
            "deliveryMethod": "pickup",
        },
        {
            "items": [{"productId": "w-tee-01", "size": "M", "quantity": 1}],
            "deliveryMethod": "pickup",
            "total": 1,
        },
    ],
    ids=["empty cart", "unknown method", "missing method", "price field", "total field"],
)
def test_quote_rejects_invalid_requests(client: TestClient, body: dict) -> None:
    assert client.post(QUOTE, json=body).status_code == 422
