import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.models import AuditLog, OrderItem, Product
from app.seed import load_catalogue
from app.services.chat_tools import execute_tool
from tests.helpers import ORDERS, place_order
from tests.test_admin_api import ADMIN_PREFIX, WEB_ORIGIN, make_user, signed_in

pytestmark = pytest.mark.usefixtures("catalogue")

TEE = "w-tee-01"  # Essential Fitted Tee, Black, LKR 3,250; w-tee-02 is the White colourway
WHITE = "w-tee-02"


@pytest.fixture
def admin(client: TestClient, db: Session) -> TestClient:
    make_user(db, "admin@example.com", "admin")
    return signed_in("admin@example.com")


@pytest.fixture
def staff(client: TestClient, db: Session) -> TestClient:
    make_user(db, "staff@example.com", "staff")
    return signed_in("staff@example.com")


def read(browser: TestClient, product_id: str = TEE) -> dict:
    response = browser.get(f"{ADMIN_PREFIX}/products/{product_id}")
    assert response.status_code == 200
    return response.json()


def edit(browser: TestClient, product_id: str = TEE, version: str | None = None, **fields):
    current = read(browser, product_id)
    body = {
        "updatedAt": version or current["updatedAt"],
        "name": current["name"],
        "price": current["price"],
        "compareAtPrice": current["compareAtPrice"],
        "description": current["description"],
        **fields,
    }
    return browser.patch(
        f"{ADMIN_PREFIX}/products/{product_id}", json=body, headers={"Origin": WEB_ORIGIN}
    )


def archive(browser: TestClient, product_id: str = TEE, version: str | None = None):
    return change_archive(browser, "archive", product_id, version)


def restore(browser: TestClient, product_id: str = TEE, version: str | None = None):
    return change_archive(browser, "restore", product_id, version)


def change_archive(browser: TestClient, action: str, product_id: str, version: str | None):
    version = version or read(browser, product_id)["updatedAt"]
    return browser.post(
        f"{ADMIN_PREFIX}/products/{product_id}/{action}",
        json={"updatedAt": version},
        headers={"Origin": WEB_ORIGIN},
    )


# ---------- reading ----------


def test_staff_can_read_products(staff: TestClient) -> None:
    body = staff.get(f"{ADMIN_PREFIX}/products").json()
    detail = read(staff)

    assert body["total"] == 17
    assert detail["name"] == "Essential Fitted Tee"
    assert detail["archived"] is False
    assert detail["sizes"] and detail["image"]
    assert {"id", "slug", "price", "compareAtPrice", "description", "updatedAt"} <= detail.keys()


def test_staff_cannot_change_anything(staff: TestClient) -> None:
    version = read(staff)["updatedAt"]
    body = {
        "updatedAt": version,
        "name": "X",
        "price": 1,
        "compareAtPrice": None,
        "description": "d",
    }
    headers = {"Origin": WEB_ORIGIN}

    assert (
        staff.patch(f"{ADMIN_PREFIX}/products/{TEE}", json=body, headers=headers).status_code == 403
    )
    for action in ("archive", "restore"):
        response = staff.post(
            f"{ADMIN_PREFIX}/products/{TEE}/{action}", json={"updatedAt": version}, headers=headers
        )
        assert response.status_code == 403
    assert read(staff)["price"] == 3250


def test_the_list_filters_by_archived_state_and_search(admin: TestClient) -> None:
    archive(admin, WHITE)

    archived = admin.get(f"{ADMIN_PREFIX}/products?archived=archived").json()
    active = admin.get(f"{ADMIN_PREFIX}/products?archived=active").json()
    tees = admin.get(f"{ADMIN_PREFIX}/products?search=fitted").json()

    assert [p["id"] for p in archived["items"]] == [WHITE]
    assert active["total"] == 16
    assert {p["id"] for p in tees["items"]} == {TEE, WHITE}
    assert admin.get(f"{ADMIN_PREFIX}/products?archived=nope").status_code == 422


def test_product_search_treats_percent_and_underscore_literally(admin: TestClient) -> None:
    assert admin.get(f"{ADMIN_PREFIX}/products?search=%25").json()["total"] == 0
    assert admin.get(f"{ADMIN_PREFIX}/products?search=_").json()["total"] == 0


def test_a_missing_product_is_a_404(admin: TestClient) -> None:
    assert admin.get(f"{ADMIN_PREFIX}/products/nope").status_code == 404


# ---------- editing ----------


def test_an_edit_saves_records_before_and_after_and_changes_the_version(
    admin: TestClient, db: Session
) -> None:
    before = read(admin)

    response = edit(admin, name="  Essential Tee  ", price=3500, compareAtPrice=4000)

    assert response.status_code == 200
    after = response.json()
    assert (after["name"], after["price"], after["compareAtPrice"]) == ("Essential Tee", 3500, 4000)
    assert after["updatedAt"] != before["updatedAt"]
    entry = db.scalars(select(AuditLog).where(AuditLog.entity == "product")).one()
    assert entry.action == "product.updated"
    assert entry.entity_id == TEE
    assert entry.details["from"] == {
        "name": "Essential Fitted Tee",
        "price": 3250,
        "compare_at_price": None,
    }
    assert entry.details["to"] == {"name": "Essential Tee", "price": 3500, "compare_at_price": 4000}


def test_the_shop_shows_the_edited_price(admin: TestClient) -> None:
    edit(admin, price=3999)

    shop = TestClient(app).get("/api/v1/products/essential-fitted-tee").json()

    assert shop["price"] == 3999


def test_an_edit_that_changes_nothing_writes_nothing(admin: TestClient, db: Session) -> None:
    before = read(admin)

    response = edit(admin)

    assert response.status_code == 200
    assert response.json()["updatedAt"] == before["updatedAt"]
    assert db.scalars(select(AuditLog)).first() is None


@pytest.mark.parametrize(
    "fields",
    [
        {"price": -1},
        {"price": 1.5},
        {"price": "3000"},
        {"price": 100_000_001},
        {"name": "   "},
        {"name": "x" * 121},
        {"description": ""},
        {"description": "x" * 2001},
        {"price": 5000, "compareAtPrice": 5000},
        {"price": 5000, "compareAtPrice": 4000},
        {"compareAtPrice": -5},
    ],
)
def test_invalid_edits_are_rejected_and_change_nothing(
    admin: TestClient, db: Session, fields: dict
) -> None:
    response = edit(admin, **fields)

    assert response.status_code == 422
    assert read(admin)["price"] == 3250
    assert db.scalars(select(AuditLog)).first() is None


def test_unknown_fields_are_rejected(admin: TestClient) -> None:
    current = read(admin)
    body = {
        "updatedAt": current["updatedAt"],
        "name": current["name"],
        "price": 1,
        "compareAtPrice": None,
        "description": current["description"],
    }

    for extra in ({"slug": "hacked"}, {"archived": True}, {"id": "other"}, {"position": 0}):
        response = admin.patch(
            f"{ADMIN_PREFIX}/products/{TEE}", json={**body, **extra}, headers={"Origin": WEB_ORIGIN}
        )
        assert response.status_code == 422

    missing = {k: v for k, v in body.items() if k != "updatedAt"}
    response = admin.patch(
        f"{ADMIN_PREFIX}/products/{TEE}", json=missing, headers={"Origin": WEB_ORIGIN}
    )
    assert response.status_code == 422


def test_a_stale_edit_is_refused(admin: TestClient, db: Session) -> None:
    make_user(db, "second@example.com", "admin")
    second = signed_in("second@example.com")
    seen_by_first = read(admin)["updatedAt"]

    assert edit(second, price=3300).status_code == 200
    late = edit(admin, version=seen_by_first, price=9999)

    assert late.status_code == 409
    assert late.json()["detail"]["code"] == "stale_product"
    assert read(admin)["price"] == 3300


def test_the_same_version_cannot_be_used_twice(admin: TestClient) -> None:
    version = read(admin)["updatedAt"]

    assert edit(admin, version=version, price=3300).status_code == 200
    assert edit(admin, version=version, price=3400).status_code == 409


# ---------- archiving ----------


def test_archiving_hides_a_product_from_every_shop_view(
    admin: TestClient, db: Session, client: TestClient
) -> None:
    shop = TestClient(app)
    assert archive(admin, TEE).status_code == 200

    assert shop.get("/api/v1/products/essential-fitted-tee").status_code == 404
    assert shop.get("/api/v1/products/essential-fitted-tee/reviews").status_code == 404
    listed = shop.get("/api/v1/products?pageSize=100").json()
    assert TEE not in {p["id"] for p in listed["items"]}
    assert listed["total"] == 16
    assert TEE not in {p["id"] for p in shop.get("/api/v1/products?id=" + TEE).json()["items"]}
    found = shop.get("/api/v1/search?q=fitted+tee").json()
    assert TEE not in {p["id"] for p in found["items"]}
    collection = shop.get("/api/v1/collections/women-t-shirts?pageSize=100").json()
    assert TEE not in {p["id"] for p in collection["items"]}
    # The other colour of the same style stays, and no longer lists the archived one.
    white = shop.get("/api/v1/products/essential-fitted-tee-white").json()
    assert [c["id"] for c in white["colourways"]] == [WHITE]


def test_archived_products_leave_related_items_and_filter_options(admin: TestClient) -> None:
    shop = TestClient(app)
    related = "/api/v1/products/heavyweight-oversized-tee/related?limit=12"
    options = "/api/v1/collections/men-t-shirts"
    assert TEE in {p["id"] for p in shop.get(related).json()}  # the check below is meaningful
    assert shop.get(options).json()["filterOptions"]["minPrice"] == 3450

    archive(admin, TEE)
    archive(admin, WHITE)
    archive(admin, "m-tee-02")  # the cheapest men's tee

    assert TEE not in {p["id"] for p in shop.get(related).json()}
    assert WHITE not in {p["id"] for p in shop.get(related).json()}
    # The cheapest men's tee is archived, so the price range shoppers can filter by moves up.
    assert shop.get(options).json()["filterOptions"]["minPrice"] == 3650


def test_archiving_hides_a_product_from_the_assistant(admin: TestClient, db: Session) -> None:
    archive(admin, TEE)
    db.expire_all()

    by_id = execute_tool(db, "get_product", {"product": TEE}, {})
    by_slug = execute_tool(db, "get_product", {"product": "essential-fitted-tee"}, {})
    search = execute_tool(db, "search_products", {"query": "fitted tee"}, {})
    browse = execute_tool(db, "search_products", {"query": "", "category": "t-shirts"}, {})

    assert by_id.is_error and by_slug.is_error
    for result in (search, browse):
        assert TEE not in [p["id"] for p in json.loads(result.content)["products"]]


def test_an_archived_product_cannot_be_priced_or_ordered(admin: TestClient) -> None:
    archive(admin, TEE)
    item = [{"productId": TEE, "size": "M", "quantity": 1}]

    quote = TestClient(app).post(
        "/api/v1/checkout/quote", json={"items": item, "deliveryMethod": "standard"}
    )
    order = place_order(TestClient(app), items=item)

    for response in (quote, order):
        assert response.status_code == 422
        assert "no longer available" in response.text


def test_an_old_order_keeps_its_archived_product(admin: TestClient, db: Session) -> None:
    shopper = TestClient(app)
    shopper.post(
        "/api/v1/auth/register",
        json={"name": "Shopper", "email": "shopper@example.com", "password": "sunrise2026"},
    )
    placed = shopper.post(ORDERS, json=__import__("tests.helpers", fromlist=["x"]).order_body())
    assert placed.status_code == 201

    edit(admin, price=9999, name="Renamed")
    assert archive(admin, TEE).status_code == 200

    mine = shopper.get(ORDERS).json()["items"][0]
    assert (mine["lines"][0]["name"], mine["lines"][0]["unitPrice"]) == (
        "Essential Fitted Tee",
        3250,
    )
    assert db.scalar(select(func.count()).select_from(OrderItem)) == 1
    assert db.get(Product, TEE) is not None


def test_restoring_brings_the_product_back(admin: TestClient) -> None:
    archive(admin, TEE)

    assert restore(admin, TEE).status_code == 200

    assert TestClient(app).get("/api/v1/products/essential-fitted-tee").status_code == 200
    assert read(admin)["archived"] is False


def test_archive_and_restore_are_audited(admin: TestClient, db: Session) -> None:
    archive(admin, TEE)
    restore(admin, TEE)

    entries = db.scalars(select(AuditLog).order_by(AuditLog.id)).all()

    assert [e.action for e in entries] == ["product.archived", "product.restored"]
    assert all(e.entity_id == TEE and e.actor_email == "admin@example.com" for e in entries)


def test_archiving_twice_or_restoring_an_active_product_is_refused(admin: TestClient) -> None:
    assert restore(admin, TEE).json()["detail"]["code"] == "not_archived"
    archive(admin, TEE)
    assert archive(admin, TEE).json()["detail"]["code"] == "already_archived"


def test_a_stale_archive_is_refused(admin: TestClient) -> None:
    stale = read(admin)["updatedAt"]
    edit(admin, price=3300)

    response = archive(admin, TEE, version=stale)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_product"
    assert read(admin)["archived"] is False


def test_archiving_from_an_untrusted_origin_is_refused(admin: TestClient) -> None:
    response = admin.post(
        f"{ADMIN_PREFIX}/products/{TEE}/archive",
        json={"updatedAt": read(admin)["updatedAt"]},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert read(admin)["archived"] is False


# ---------- the seed must not undo admin work ----------


def test_running_the_seed_again_keeps_edits_and_archived_products(
    admin: TestClient, db: Session
) -> None:
    edit(admin, name="Renamed", price=4000)
    archive(admin, WHITE)

    load_catalogue(db)

    assert read(admin)["name"] == "Renamed"
    assert read(admin, WHITE)["archived"] is True
    assert db.scalar(select(func.count()).select_from(Product)) == 17


def test_a_product_with_orders_survives_the_seed(admin: TestClient, db: Session) -> None:
    assert place_order(TestClient(app)).status_code == 201

    load_catalogue(db)

    assert db.get(Product, TEE) is not None
