import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete, func, select, text, update
from sqlalchemy.orm import Session

from app.main import app
from app.models import AuditLog, Order, OrderStatusHistory, User, UserSession
from app.services import admin_orders
from app.services.admin import AdminError
from tests.helpers import ORDERS, place_order
from tests.test_admin_api import ADMIN_PREFIX, WEB_ORIGIN, make_user, signed_in

pytestmark = pytest.mark.usefixtures("catalogue")


@pytest.fixture
def staff(client: TestClient, db: Session) -> TestClient:
    make_user(db, "staff@example.com", "staff")
    return signed_in("staff@example.com")


@pytest.fixture
def customer(client: TestClient, db: Session) -> TestClient:
    make_user(db, "customer@example.com", "customer")
    return signed_in("customer@example.com")


def new_order(**overrides) -> str:
    response = place_order(TestClient(app), **overrides)
    assert response.status_code == 201
    return response.json()["reference"]


def move(browser: TestClient, reference: str, expected: str, status: str):
    return browser.patch(
        f"{ADMIN_PREFIX}/orders/{reference}/status",
        json={"expectedStatus": expected, "status": status},
        headers={"Origin": WEB_ORIGIN},
    )


def set_status(db: Session, reference: str, status: str) -> None:
    db.execute(update(Order).where(Order.reference == reference).values(status=status))
    # Committed (into the test's outer transaction), because a refused change rolls back.
    db.commit()


# ---------- reading ----------


def test_customers_cannot_read_orders_here(customer: TestClient) -> None:
    reference = new_order()

    assert customer.get(f"{ADMIN_PREFIX}/orders").status_code == 403
    assert customer.get(f"{ADMIN_PREFIX}/orders/{reference}").status_code == 403


def test_staff_list_orders_newest_first(staff: TestClient) -> None:
    first, second = new_order(), new_order()

    body = staff.get(f"{ADMIN_PREFIX}/orders").json()

    assert body["total"] == 2
    assert [o["reference"] for o in body["items"]] == [second, first]
    assert {"reference", "status", "email", "fullName", "total", "createdAt"} == body["items"][
        0
    ].keys()


def test_orders_filter_by_status(staff: TestClient, db: Session) -> None:
    new_order()
    shipped = new_order()
    set_status(db, shipped, "shipped")

    body = staff.get(f"{ADMIN_PREFIX}/orders?status=shipped").json()

    assert [o["reference"] for o in body["items"]] == [shipped]
    assert staff.get(f"{ADMIN_PREFIX}/orders?status=lost").status_code == 422


def test_orders_search_by_reference_email_or_name(staff: TestClient) -> None:
    mine = new_order(email="kamal@shop.lk", fullName="Kamal Silva")
    new_order(email="other@example.com")

    by_email = staff.get(f"{ADMIN_PREFIX}/orders?search=kamal@").json()
    by_name = staff.get(f"{ADMIN_PREFIX}/orders?search=SILVA").json()
    by_reference = staff.get(f"{ADMIN_PREFIX}/orders?search={mine.lower()}").json()

    for body in (by_email, by_name, by_reference):
        assert [o["reference"] for o in body["items"]] == [mine]


def test_order_search_treats_percent_and_underscore_literally(staff: TestClient) -> None:
    new_order()

    assert staff.get(f"{ADMIN_PREFIX}/orders?search=%25").json()["total"] == 0
    assert staff.get(f"{ADMIN_PREFIX}/orders?search=_").json()["total"] == 0


def test_order_detail_has_lines_totals_history_and_next_steps(staff: TestClient) -> None:
    reference = new_order()

    body = staff.get(f"{ADMIN_PREFIX}/orders/{reference}").json()

    assert body["reference"] == reference
    assert body["lines"][0]["quantity"] == 2
    assert body["total"] == body["subtotal"] + body["shipping"]
    assert body["history"] == []
    assert body["allowedNext"] == ["confirmed", "cancelled"]
    assert "idempotencyKey" not in body


def test_a_missing_order_is_a_404(staff: TestClient) -> None:
    assert staff.get(f"{ADMIN_PREFIX}/orders/WA-NOPE").status_code == 404
    assert move(staff, "WA-NOPE", "pending", "confirmed").status_code == 404


# ---------- status rules ----------

ALLOWED = [
    ("pending", "confirmed"),
    ("pending", "cancelled"),
    ("confirmed", "shipped"),
    ("confirmed", "cancelled"),
    ("shipped", "delivered"),
]
STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
FORBIDDEN = [(a, b) for a in STATUSES for b in STATUSES if (a, b) not in ALLOWED]


@pytest.mark.parametrize(("start", "end"), ALLOWED)
def test_allowed_moves_work_and_are_recorded(
    staff: TestClient, db: Session, start: str, end: str
) -> None:
    reference = new_order()
    set_status(db, reference, start)

    response = move(staff, reference, start, end)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == end
    assert body["allowedNext"] == admin_orders.allowed_next(end)
    assert [(h["fromStatus"], h["toStatus"], h["actorEmail"]) for h in body["history"]] == [
        (start, end, "staff@example.com")
    ]
    entry = db.scalars(select(AuditLog).where(AuditLog.entity == "order")).one()
    assert (entry.action, entry.entity_id, entry.actor_email) == (
        "order.status_changed",
        reference,
        "staff@example.com",
    )
    assert entry.details == {"from": start, "to": end}


@pytest.mark.parametrize(("start", "end"), FORBIDDEN)
def test_every_other_move_is_refused_and_changes_nothing(
    staff: TestClient, db: Session, start: str, end: str
) -> None:
    reference = new_order()
    set_status(db, reference, start)

    response = move(staff, reference, start, end)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_transition"
    assert db.scalar(select(Order.status).where(Order.reference == reference)) == start
    assert db.scalars(select(OrderStatusHistory)).first() is None
    assert db.scalars(select(AuditLog)).first() is None


def test_a_shipped_order_cannot_be_cancelled(staff: TestClient, db: Session) -> None:
    reference = new_order()
    set_status(db, reference, "shipped")

    assert move(staff, reference, "shipped", "cancelled").status_code == 409


def test_a_stale_screen_cannot_overwrite_a_newer_change(staff: TestClient, db: Session) -> None:
    reference = new_order()
    other = make_user(db, "other@example.com", "staff")
    assert other.role == "staff"
    second_staff = signed_in("other@example.com")

    assert move(second_staff, reference, "pending", "confirmed").status_code == 200
    late = move(staff, reference, "pending", "cancelled")

    assert late.status_code == 409
    assert late.json()["detail"]["code"] == "stale_status"
    assert late.json()["detail"]["status"] == "confirmed"
    assert db.scalar(select(Order.status).where(Order.reference == reference)) == "confirmed"
    assert len(db.scalars(select(OrderStatusHistory)).all()) == 1


def test_the_same_click_twice_changes_it_only_once(staff: TestClient, db: Session) -> None:
    reference = new_order()

    assert move(staff, reference, "pending", "confirmed").status_code == 200
    assert move(staff, reference, "pending", "confirmed").status_code == 409
    assert len(db.scalars(select(OrderStatusHistory)).all()) == 1


def test_a_status_change_takes_only_the_two_statuses(staff: TestClient) -> None:
    reference = new_order()

    for body in (
        {"expectedStatus": "pending", "status": "confirmed", "total": 1},
        {"expectedStatus": "pending", "status": "lost"},
        {"status": "confirmed"},
    ):
        response = staff.patch(
            f"{ADMIN_PREFIX}/orders/{reference}/status", json=body, headers={"Origin": WEB_ORIGIN}
        )
        assert response.status_code == 422


def test_a_status_change_never_touches_prices_or_lines(staff: TestClient, db: Session) -> None:
    reference = new_order()
    before = staff.get(f"{ADMIN_PREFIX}/orders/{reference}").json()

    move(staff, reference, "pending", "confirmed")
    after = staff.get(f"{ADMIN_PREFIX}/orders/{reference}").json()

    for field in ("lines", "subtotal", "shipping", "total", "email", "address1"):
        assert before[field] == after[field]


def test_a_customer_and_a_guest_cannot_change_status(customer: TestClient) -> None:
    reference = new_order()

    assert move(customer, reference, "pending", "confirmed").status_code == 403
    assert move(TestClient(app), reference, "pending", "confirmed").status_code == 401


def test_a_status_change_from_an_untrusted_origin_is_refused(staff: TestClient) -> None:
    reference = new_order()

    response = staff.patch(
        f"{ADMIN_PREFIX}/orders/{reference}/status",
        json={"expectedStatus": "pending", "status": "confirmed"},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403


def test_the_customers_own_view_shows_the_new_status(db: Session, staff: TestClient) -> None:
    shopper = TestClient(app)
    shopper.post(
        "/api/v1/auth/register",
        json={"name": "Shopper", "email": "shopper@example.com", "password": "sunrise2026"},
    )
    reference = shopper.post(
        ORDERS, json=__import__("tests.helpers", fromlist=["x"]).order_body()
    ).json()["reference"]

    move(staff, reference, "pending", "confirmed")

    mine = shopper.get(ORDERS).json()["items"]
    assert [(o["reference"], o["status"]) for o in mine] == [(reference, "confirmed")]


def test_deleting_the_actor_keeps_the_history_entry(staff: TestClient, db: Session) -> None:
    reference = new_order()
    move(staff, reference, "pending", "confirmed")
    user = db.scalar(select(User).where(User.email == "staff@example.com"))
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.delete(user)
    db.flush()

    entry = db.scalars(select(OrderStatusHistory)).one()
    assert entry.actor_id is None
    assert entry.actor_email == "staff@example.com"


def test_two_staff_acting_at_the_same_moment_cannot_both_win(engine: Engine) -> None:
    """A real race on separate connections: the row lock makes the second one see the first."""
    with Session(engine) as setup:
        people = [
            User(name=n, email=f"race-{n}@example.com", password_hash="x", role="staff")
            for n in ("a", "b")
        ]
        order = Order(
            reference="WA-RACE01",
            email="r@example.com",
            phone="0771234567",
            full_name="R",
            address1="a",
            city="c",
            province="Western",
            district="Colombo",
            postal_code="10250",
            delivery_method="standard",
            payment_method="cod",
            subtotal=1,
            shipping=0,
            total=1,
        )
        setup.add_all([*people, order])
        setup.commit()
        actor_ids = [person.id for person in people]

    outcomes: list[str] = []
    start = threading.Barrier(2)

    def act(actor_id: int, target: str) -> None:
        with Session(engine) as session:
            actor = session.get(User, actor_id)
            start.wait()
            try:
                admin_orders.change_status(
                    session,
                    actor=actor,
                    reference="WA-RACE01",
                    expected_status="pending",
                    new_status=target,
                )
                outcomes.append("ok")
            except AdminError as error:
                outcomes.append(str(error.code))

    try:
        threads = [
            threading.Thread(target=act, args=(actor_ids[0], "confirmed")),
            threading.Thread(target=act, args=(actor_ids[1], "cancelled")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        with Session(engine) as check:
            changes = check.scalar(select(func.count()).select_from(OrderStatusHistory))
        assert sorted(outcomes) == ["ok", "stale_status"]
        assert changes == 1
    finally:
        with Session(engine) as cleanup:
            # DELETE is refused by design; the disposable test database is emptied with TRUNCATE.
            cleanup.execute(text("TRUNCATE audit_log"))
            cleanup.execute(delete(Order).where(Order.reference == "WA-RACE01"))
            cleanup.execute(delete(User).where(User.email.like("race-%@example.com")))
            cleanup.commit()
