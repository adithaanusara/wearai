from fastapi.testclient import TestClient

ORDERS = "/api/v1/orders"


def order_body(**overrides) -> dict:
    """A valid order: 2 x Essential Fitted Tee (M) for LKR 6,500, standard delivery."""
    body = {
        "items": [{"productId": "w-tee-01", "size": "M", "quantity": 2}],
        "deliveryMethod": "standard",
        "paymentMethod": "cod",
        "email": "Nimali@Example.com",
        "phone": "077 123 4567",
        "fullName": "Nimali Perera",
        "address1": "12 Temple Road",
        "address2": "",
        "city": "Nugegoda",
        "province": "Western",
        "district": "Colombo",
        "postalCode": "10250",
    }
    body.update(overrides)
    return body


def place_order(client: TestClient, headers: dict | None = None, **overrides):
    return client.post(ORDERS, json=order_body(**overrides), headers=headers or {})


def sign_up(client: TestClient, email: str = "owner@example.com") -> None:
    """Registers a user; the client keeps the session cookie."""
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Owner", "email": email, "password": "sunrise2026"},
    )
    assert response.status_code == 201
