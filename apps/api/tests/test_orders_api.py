import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.main import app
from app.models import Order, OrderItem, Product, User
from app.seed import CATALOGUE_PATH
from app.services import orders as order_service
from tests.helpers import ORDERS, order_body, place_order, sign_up

pytestmark = pytest.mark.usefixtures("catalogue")

REFERENCE = re.compile(r"^WA-[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{8}$")


# ---------- creating an order ----------


def test_a_guest_can_place_an_order(client: TestClient, db: Session) -> None:
    response = place_order(client)

    body = response.json()
    assert response.status_code == 201
    assert REFERENCE.match(body["reference"])
    assert body["status"] == "pending"
    assert (body["subtotal"], body["shipping"], body["total"]) == (6500, 450, 6950)
    assert body["lines"] == [
        {
            "productId": "w-tee-01",
            "name": "Essential Fitted Tee",
            "colour": "Black",
            "size": "M",
            "unitPrice": 3250,
            "quantity": 2,
            "lineTotal": 6500,
        }
    ]
    assert db.scalars(select(Order)).one().user_id is None
    assert "set-cookie" not in response.headers
    assert response.headers["cache-control"] == "no-store"


def test_details_are_cleaned_up_before_saving(client: TestClient, db: Session) -> None:
    body = place_order(client, phone="077-123-4567", fullName="  Nimali Perera ").json()

    assert body["email"] == "nimali@example.com"
    assert body["phone"] == "+94771234567"
    assert body["fullName"] == "Nimali Perera"
    assert db.scalars(select(Order)).one().phone == "+94771234567"


def test_the_response_does_not_expose_internal_fields(client: TestClient) -> None:
    body = place_order(client, headers={"Idempotency-Key": "abcdefgh12345678"}).json()

    assert not {"id", "userId", "idempotencyKey", "requestFingerprint"} & body.keys()


def test_a_signed_in_order_belongs_to_the_account(client: TestClient, db: Session) -> None:
    sign_up(client)

    reference = place_order(client).json()["reference"]

    order = db.scalars(select(Order)).one()
    assert order.user_id == db.scalars(select(User)).one().id
    assert client.get(f"{ORDERS}/{reference}").status_code == 200


def test_references_are_unique(client: TestClient, db: Session) -> None:
    references = {place_order(client).json()["reference"] for _ in range(25)}

    assert len(references) == 25


def test_a_reference_collision_is_retried(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sequence = iter(["WA-AAAAAAAA", "WA-AAAAAAAA", "WA-BBBBBBBB"])
    monkeypatch.setattr(order_service, "_new_reference", lambda: next(sequence))

    first = place_order(client).json()["reference"]
    second = place_order(client).json()["reference"]

    assert (first, second) == ("WA-AAAAAAAA", "WA-BBBBBBBB")


def test_gives_up_when_no_free_reference_can_be_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(order_service, "_new_reference", lambda: "WA-CCCCCCCC")
    assert place_order(client).status_code == 201

    with pytest.raises(RuntimeError, match="order reference"):
        place_order(client)


# ---------- the server decides the price ----------


@pytest.mark.parametrize(
    "extra",
    [
        {"total": 1},
        {"shipping": 0},
        {"subtotal": 1},
        {"status": "delivered"},
        {"userId": 1},
        {"reference": "WA-HACKED1"},
    ],
    ids=["total", "shipping", "subtotal", "status", "user", "reference"],
)
def test_client_supplied_amounts_and_fields_are_rejected(
    client: TestClient, db: Session, extra: dict
) -> None:
    response = place_order(client, **extra)

    assert response.status_code == 422
    assert db.scalars(select(Order)).all() == []


@pytest.mark.parametrize("field", ["price", "unitPrice", "lineTotal", "name"])
def test_a_price_on_a_line_is_rejected(client: TestClient, field: str) -> None:
    items = [{"productId": "w-tee-01", "size": "M", "quantity": 1, field: 1}]

    assert place_order(client, items=items).status_code == 422


def test_the_price_comes_from_the_database_not_the_request(client: TestClient, db: Session) -> None:
    db.execute(update(Product).where(Product.id == "w-tee-01").values(price=4000))
    db.commit()

    body = place_order(client).json()

    assert body["lines"][0]["unitPrice"] == 4000
    assert body["subtotal"] == 8000


def test_history_does_not_change_when_the_catalogue_does(client: TestClient, db: Session) -> None:
    sign_up(client)
    reference = place_order(client).json()["reference"]

    db.execute(
        update(Product)
        .where(Product.id == "w-tee-01")
        .values(price=9999, name="Renamed", colour="Pink")
    )
    db.commit()

    line = client.get(f"{ORDERS}/{reference}").json()["lines"][0]
    assert (line["name"], line["colour"], line["unitPrice"]) == (
        "Essential Fitted Tee",
        "Black",
        3250,
    )
    assert client.get(f"{ORDERS}/{reference}").json()["total"] == 6950


def test_shipping_follows_the_delivery_method(client: TestClient) -> None:
    express = place_order(client, deliveryMethod="express").json()
    pickup = place_order(client, deliveryMethod="pickup").json()
    free = place_order(
        client, items=[{"productId": "m-hood-01", "size": "L", "quantity": 2}]
    ).json()

    assert express["shipping"] == 950 and express["total"] == 7450
    assert pickup["shipping"] == 0 and pickup["total"] == 6500
    assert (free["subtotal"], free["shipping"], free["total"]) == (18900, 0, 18900)


# ---------- the cart ----------


def test_unknown_products_and_unavailable_sizes_are_rejected(
    client: TestClient, db: Session
) -> None:
    unknown = place_order(client, items=[{"productId": "nope", "size": "M", "quantity": 1}])
    bad_size = place_order(
        client,
        items=[
            {"productId": "w-tee-01", "size": "M", "quantity": 1},
            {"productId": "w-hood-01", "size": "XL", "quantity": 1},
        ],
    )

    assert unknown.status_code == bad_size.status_code == 422
    assert unknown.json()["detail"][0]["loc"] == ["body", "items", 0, "productId"]
    assert bad_size.json()["detail"][0]["loc"] == ["body", "items", 1, "size"]
    assert db.scalars(select(Order)).all() == []


@pytest.mark.parametrize("quantity", [0, -1, 11, 1.5, "2", True, None])
def test_quantity_must_be_a_whole_number_from_one_to_ten(client: TestClient, quantity) -> None:
    items = [{"productId": "w-tee-01", "size": "M", "quantity": quantity}]

    assert place_order(client, items=items).status_code == 422


def test_quantity_limits_are_inclusive(client: TestClient) -> None:
    for quantity in (1, 10):
        items = [{"productId": "w-tee-01", "size": "M", "quantity": quantity}]
        assert place_order(client, items=items).status_code == 201


def test_empty_and_duplicate_carts_are_rejected(client: TestClient) -> None:
    line = {"productId": "w-tee-01", "size": "M", "quantity": 1}

    assert place_order(client, items=[]).status_code == 422
    assert place_order(client, items=[line, line]).status_code == 422
    # The same product in a different size is a different line.
    assert place_order(client, items=[line, {**line, "size": "L"}]).status_code == 201


def test_the_number_of_lines_is_limited(client: TestClient) -> None:
    catalogue = json.loads(CATALOGUE_PATH.read_text())["products"]
    lines = [
        {"productId": p["id"], "size": size, "quantity": 1}
        for p in catalogue
        for size in p["sizes"]
    ]
    assert len(lines) >= 51

    assert place_order(client, items=lines[:50]).status_code == 201
    assert place_order(client, items=lines[:51]).status_code == 422


# ---------- validation (the same rules as the website) ----------


@pytest.mark.parametrize("phone", ["0771234567", "077-123-4567", "+94771234567", "+94 77 123 4567"])
def test_valid_sri_lankan_mobile_numbers(client: TestClient, phone: str) -> None:
    response = place_order(client, phone=phone)

    assert response.status_code == 201
    assert response.json()["phone"] == "+94771234567"


@pytest.mark.parametrize(
    "phone",
    [
        "12345",
        "0112345678",
        "077123456",
        "+9477123456789",
        "",
        "abc",
        "０７７１２３４５６７",  # fullwidth digits
        "07٧1234567",  # an Arabic-Indic digit
    ],
)
def test_invalid_phone_numbers(client: TestClient, phone: str) -> None:
    assert place_order(client, phone=phone).status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "nimali@"},
        {"email": ""},
        {"fullName": "  "},
        {"address1": ""},
        {"city": " "},
        {"postalCode": "1025"},
        {"postalCode": "1025A"},
        {"postalCode": "102500"},
        {"postalCode": "１０２５０"},  # fullwidth digits look right but are not ASCII
        {"postalCode": "١٠٢٥٠"},  # Arabic-Indic digits
        {"province": "Atlantis"},
        {"province": "Central"},  # Colombo is not in Central
        {"district": "Kandy"},  # Kandy is not in Western
        {"district": ""},
        {"deliveryMethod": "drone"},
        {"paymentMethod": "bitcoin"},
        {"paymentMethod": ""},
        {"fullName": "x" * 121},
        {"address1": "x" * 201},
    ],
)
def test_invalid_details_are_rejected(client: TestClient, db: Session, overrides: dict) -> None:
    assert place_order(client, **overrides).status_code == 422
    assert db.scalars(select(Order)).all() == []


def test_a_district_mismatch_is_reported_on_the_district_field(client: TestClient) -> None:
    response = place_order(client, district="Kandy")  # Kandy is in Central, not Western

    assert response.json()["detail"][0]["loc"] == ["body", "district"]


def test_an_invalid_province_also_flags_the_district(client: TestClient) -> None:
    fields = {d["loc"][-1] for d in place_order(client, province="Atlantis").json()["detail"]}

    assert fields == {"province", "district"}  # the same as the website


def test_the_second_address_line_is_optional(client: TestClient) -> None:
    body = order_body()
    del body["address2"]

    assert client.post(ORDERS, json=body).status_code == 201


def test_missing_required_fields_are_rejected(client: TestClient) -> None:
    assert client.post(ORDERS, json={}).status_code == 422
    assert client.post(ORDERS, content=b"not json").status_code == 422


def test_errors_never_echo_what_was_submitted(client: TestClient) -> None:
    response = place_order(client, phone="secret-number-123")

    assert "secret-number-123" not in response.text


# ---------- idempotency ----------


def test_a_retry_with_the_same_key_returns_the_original_order(
    client: TestClient, db: Session
) -> None:
    headers = {"Idempotency-Key": "abcdefgh12345678"}

    first = place_order(client, headers=headers)
    second = place_order(client, headers=headers)

    assert (first.status_code, second.status_code) == (201, 200)
    assert second.json() == first.json()
    assert len(db.scalars(select(Order)).all()) == 1


def test_without_a_key_two_identical_requests_make_two_orders(
    client: TestClient, db: Session
) -> None:
    place_order(client)
    place_order(client)

    assert len(db.scalars(select(Order)).all()) == 2


def test_reusing_a_key_for_a_different_order_is_a_conflict(client: TestClient, db: Session) -> None:
    headers = {"Idempotency-Key": "abcdefgh12345678"}
    place_order(client, headers=headers)

    response = place_order(client, headers=headers, deliveryMethod="express")

    assert response.status_code == 409
    assert len(db.scalars(select(Order)).all()) == 1


def test_a_key_cannot_be_replayed_by_a_different_account(client: TestClient, db: Session) -> None:
    headers = {"Idempotency-Key": "abcdefgh12345678"}
    place_order(client, headers=headers)  # as a guest
    sign_up(client)

    response = place_order(client, headers=headers)  # same payload, but a signed-in user

    assert response.status_code == 409


@pytest.mark.parametrize("key", ["short", "x" * 65, "has spaces here", "semi;colon;1234"])
def test_malformed_idempotency_keys_are_rejected(client: TestClient, key: str) -> None:
    assert place_order(client, headers={"Idempotency-Key": key}).status_code == 422


# ---------- reading orders ----------


def test_listing_requires_a_session(client: TestClient) -> None:
    place_order(client)

    assert client.get(ORDERS).status_code == 401
    assert client.get(f"{ORDERS}/WA-ANYTHING").status_code == 401


def test_a_user_sees_only_their_own_orders_newest_first(client: TestClient) -> None:
    sign_up(client)
    first = place_order(client).json()["reference"]
    second = place_order(client, deliveryMethod="express").json()["reference"]
    guest = TestClient(app)
    place_order(guest)  # a guest order belongs to nobody

    body = client.get(ORDERS).json()

    assert [o["reference"] for o in body["items"]] == [second, first]
    assert body["total"] == 2


def test_orders_are_paginated(client: TestClient) -> None:
    sign_up(client)
    references = [place_order(client).json()["reference"] for _ in range(5)]

    page_one = client.get(f"{ORDERS}?pageSize=2").json()
    page_three = client.get(f"{ORDERS}?pageSize=2&page=3").json()

    assert [o["reference"] for o in page_one["items"]] == references[::-1][:2]
    assert [o["reference"] for o in page_three["items"]] == references[:1]
    assert page_one["total"] == 5
    assert client.get(f"{ORDERS}?pageSize=101").status_code == 422


def test_another_users_order_looks_like_a_missing_one(client: TestClient) -> None:
    sign_up(client, "alice@example.com")
    reference = place_order(client).json()["reference"]
    mallory = TestClient(app)
    sign_up(mallory, "mallory@example.com")

    theirs = mallory.get(f"{ORDERS}/{reference}")
    missing = mallory.get(f"{ORDERS}/WA-NOTREAL1")

    assert theirs.status_code == missing.status_code == 404
    assert theirs.json() == missing.json() == {"detail": "Order not found"}
    assert mallory.get(ORDERS).json()["items"] == []


def test_a_guest_cannot_read_an_order_by_reference(client: TestClient) -> None:
    sign_up(client)
    reference = place_order(client).json()["reference"]

    assert TestClient(app).get(f"{ORDERS}/{reference}").status_code == 401


def test_order_reads_are_not_cacheable(client: TestClient) -> None:
    sign_up(client)
    reference = place_order(client).json()["reference"]

    assert client.get(f"{ORDERS}/{reference}").headers["cache-control"] == "no-store"


def test_orders_are_kept_when_the_account_is_deleted(client: TestClient, db: Session) -> None:
    sign_up(client)
    place_order(client)

    db.delete(db.scalars(select(User)).one())
    db.commit()

    assert db.scalars(select(Order)).one().user_id is None


# ---------- CSRF ----------


@pytest.mark.parametrize("origin", ["https://evil.example", "null"])
def test_orders_from_untrusted_origins_are_rejected(
    client: TestClient, db: Session, origin: str
) -> None:
    response = place_order(client, headers={"Origin": origin})

    assert response.status_code == 403
    assert db.scalars(select(Order)).all() == []


def test_the_website_origin_is_accepted(client: TestClient) -> None:
    assert place_order(client, headers={"Origin": "http://localhost:3000"}).status_code == 201


# ---------- the database refuses bad data too ----------


def make_order(**overrides) -> Order:
    values = {
        "reference": "WA-TESTTEST",
        "email": "a@example.com",
        "phone": "+94771234567",
        "full_name": "A",
        "address1": "B",
        "city": "C",
        "province": "Western",
        "district": "Colombo",
        "postal_code": "10250",
        "delivery_method": "standard",
        "payment_method": "cod",
        "subtotal": 1000,
        "shipping": 450,
        "total": 1450,
    }
    return Order(**{**values, **overrides})


@pytest.mark.parametrize(
    "overrides",
    [
        {"total": 1},
        {"subtotal": -1, "total": 449},
        {"shipping": -1, "total": 999},
        {"status": "bogus"},
    ],
    ids=["total does not add up", "negative subtotal", "negative shipping", "bad status"],
)
def test_order_constraints(db: Session, overrides: dict) -> None:
    db.add(make_order(**overrides))

    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize(
    "overrides",
    [{"quantity": 0}, {"quantity": 11}, {"unit_price": -5, "line_total": -5}, {"line_total": 1}],
)
def test_order_item_constraints(db: Session, overrides: dict) -> None:
    item = {
        "product_id": "w-tee-01",
        "product_name": "Tee",
        "colour": "Black",
        "size": "M",
        "unit_price": 100,
        "quantity": 1,
        "line_total": 100,
        "position": 0,
    }
    order = make_order()
    order.items = [OrderItem(**{**item, **overrides})]
    db.add(order)

    with pytest.raises(IntegrityError):
        db.flush()


def test_a_product_that_was_ordered_cannot_be_deleted(client: TestClient, db: Session) -> None:
    place_order(client)

    db.delete(db.get(Product, "w-tee-01"))

    with pytest.raises(IntegrityError):
        db.flush()
