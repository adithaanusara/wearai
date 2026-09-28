"""Placing a card order returns the PayHere checkout form; other methods do not."""

import pytest
from fastapi.testclient import TestClient

from app import payhere
from app.config import settings
from tests.helpers import order_body, place_order

pytestmark = pytest.mark.usefixtures("catalogue")


@pytest.fixture(autouse=True)
def payhere_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "payhere_merchant_id", "1211149")
    monkeypatch.setattr(settings, "payhere_merchant_secret", "test-secret")
    monkeypatch.setattr(settings, "site_url", "http://localhost:3000")
    monkeypatch.setattr(settings, "api_public_url", "http://localhost:8000")


def test_a_card_order_returns_a_signed_checkout_form(client: TestClient) -> None:
    response = place_order(client, paymentMethod="card")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["paymentStatus"] == "unpaid"
    checkout = body["payhere"]
    assert checkout["action"] == "https://sandbox.payhere.lk/pay/checkout"
    assert checkout["merchantId"] == "1211149"
    assert checkout["orderId"] == body["reference"]
    assert checkout["amount"] == payhere.format_amount(body["total"])
    assert checkout["hash"] == payhere.checkout_hash(body["reference"], body["total"])
    assert (
        checkout["returnUrl"] == f"http://localhost:3000/checkout/success?order={body['reference']}"
    )
    assert (
        checkout["cancelUrl"] == f"http://localhost:3000/checkout/cancel?order={body['reference']}"
    )
    assert checkout["notifyUrl"] == "http://localhost:8000/api/v1/payments/payhere/notify"
    assert checkout["email"] == body["email"]


def test_cash_on_delivery_gets_no_checkout_form(client: TestClient) -> None:
    response = place_order(client, paymentMethod="cod")

    assert response.json()["payhere"] is None


def test_bank_transfer_gets_no_checkout_form(client: TestClient) -> None:
    response = place_order(client, paymentMethod="bank-transfer")

    assert response.json()["payhere"] is None


def test_card_payment_is_refused_when_payhere_is_not_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "payhere_merchant_secret", None)

    response = place_order(client, paymentMethod="card")

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "payment_method_unavailable"


def test_a_single_word_name_still_gets_a_last_name(client: TestClient) -> None:
    response = place_order(client, paymentMethod="card", fullName="Buddhika")

    assert response.status_code == 201
    # A last name PayHere will still accept, even though the shopper only gave one word.
    assert response.json()["payhere"]["lastName"] == "."
    assert response.json()["payhere"]["firstName"] == "Buddhika"


def test_the_hash_uses_the_real_total_not_a_client_supplied_one(client: TestClient) -> None:
    body = order_body(paymentMethod="card")
    response = client.post("/api/v1/orders", json=body)

    checkout = response.json()["payhere"]
    assert checkout["amount"] == payhere.format_amount(response.json()["total"])
    # Nothing the shopper sent chose the amount that gets signed.
    assert "amount" not in body and "total" not in body


def test_a_retry_of_an_idempotent_card_order_returns_the_same_checkout_form(
    client: TestClient,
) -> None:
    headers = {"Idempotency-Key": "retry-card-order-1"}
    first = client.post("/api/v1/orders", json=order_body(paymentMethod="card"), headers=headers)
    second = client.post("/api/v1/orders", json=order_body(paymentMethod="card"), headers=headers)

    assert second.status_code == 200
    assert second.json()["payhere"]["hash"] == first.json()["payhere"]["hash"]


def test_getting_an_existing_order_never_repeats_the_checkout_form(client: TestClient) -> None:
    from tests.helpers import sign_up

    sign_up(client, email="cardbuyer@example.com")
    response = client.post(
        "/api/v1/orders", json=order_body(paymentMethod="card", email="cardbuyer@example.com")
    )
    reference = response.json()["reference"]

    fetched = client.get(f"/api/v1/orders/{reference}")

    assert fetched.json()["payhere"] is None
