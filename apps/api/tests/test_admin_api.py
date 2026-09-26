import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.main import app
from app.models import AuditLog, User, UserSession
from app.services import audit

PASSWORD = "sunrise2026"
WEB_ORIGIN = "http://localhost:3000"
ADMIN_PREFIX = "/api/v1/admin"


def make_user(db: Session, email: str, role: str = "customer") -> User:
    """Registers through the real endpoint, then sets the role directly, as the CLI does."""
    response = TestClient(app).post(
        "/api/v1/auth/register",
        json={"name": email.split("@")[0], "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    user = db.scalar(select(User).where(User.email == email))
    user.role = role
    db.flush()
    return user


def signed_in(email: str) -> TestClient:
    """A separate browser: its own cookie jar."""
    browser = TestClient(app)
    response = browser.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return browser


@pytest.fixture
def people(client: TestClient, db: Session) -> dict[str, TestClient]:
    make_user(db, "customer@example.com", "customer")
    make_user(db, "staff@example.com", "staff")
    make_user(db, "admin@example.com", "admin")
    return {
        "guest": TestClient(app),
        "customer": signed_in("customer@example.com"),
        "staff": signed_in("staff@example.com"),
        "admin": signed_in("admin@example.com"),
    }


def admin_routes() -> list[tuple[str, str, str]]:
    """(method, path, least role) for every route under /admin, read from the app's own schema."""
    found = []
    for path, operations in app.openapi()["paths"].items():
        if not path.startswith(ADMIN_PREFIX):
            continue
        for method, operation in operations.items():
            roles = [tag for tag in operation["tags"] if tag.startswith("role:")]
            assert len(roles) == 1, f"{method} {path} must declare exactly one role tag"
            found.append((method.upper(), path.replace("{user_id}", "1"), roles[0][5:]))
    return found


def call(browser: TestClient, method: str, path: str):
    body = {"role": "staff"} if method == "PATCH" else None
    return browser.request(method, path, json=body, headers={"Origin": WEB_ORIGIN})


# ---------- the route walk: no route can be added without protection ----------


def test_there_are_admin_routes_to_check() -> None:
    assert len(admin_routes()) >= 5


@pytest.mark.parametrize(("method", "path", "least"), admin_routes())
def test_every_admin_route_enforces_its_role(
    people: dict[str, TestClient], method: str, path: str, least: str
) -> None:
    assert call(people["guest"], method, path).status_code == 401
    assert call(people["customer"], method, path).status_code == 403
    staff = call(people["staff"], method, path).status_code
    if least == "admin":
        assert staff == 403
    else:
        assert staff == 200
    assert call(people["admin"], method, path).status_code != 403


def test_every_admin_route_rejects_untrusted_origins(people: dict[str, TestClient]) -> None:
    for method, path, _ in admin_routes():
        response = people["admin"].request(
            method, path, json={"role": "staff"}, headers={"Origin": "https://evil.example"}
        )
        assert response.status_code == 403, f"{method} {path}"


def test_the_role_is_read_from_the_database_on_every_request(
    people: dict[str, TestClient], db: Session
) -> None:
    assert people["staff"].get(f"{ADMIN_PREFIX}/me").status_code == 200

    # Demoted behind the session's back, the very next request is refused.
    db.execute(update(User).where(User.email == "staff@example.com").values(role="customer"))
    assert people["staff"].get(f"{ADMIN_PREFIX}/me").status_code == 403


def test_auth_me_reports_the_role(people: dict[str, TestClient]) -> None:
    assert people["staff"].get("/api/v1/auth/me").json()["role"] == "staff"


def test_registering_never_grants_a_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Sneaky", "email": "s@example.com", "password": PASSWORD, "role": "admin"},
    )

    assert response.status_code in (201, 422)
    if response.status_code == 201:
        assert response.json()["role"] == "customer"


# ---------- users ----------


def test_admin_lists_and_filters_users(people: dict[str, TestClient]) -> None:
    body = people["admin"].get(f"{ADMIN_PREFIX}/users").json()
    assert body["total"] == 3
    assert {user["role"] for user in body["items"]} == {"customer", "staff", "admin"}

    only_staff = people["admin"].get(f"{ADMIN_PREFIX}/users?role=staff").json()
    assert [user["email"] for user in only_staff["items"]] == ["staff@example.com"]
    assert "passwordHash" not in people["admin"].get(f"{ADMIN_PREFIX}/users").text


def test_user_search_treats_percent_and_underscore_literally(
    people: dict[str, TestClient],
) -> None:
    assert people["admin"].get(f"{ADMIN_PREFIX}/users?search=%25").json()["total"] == 0
    assert people["admin"].get(f"{ADMIN_PREFIX}/users?search=_").json()["total"] == 0
    assert people["admin"].get(f"{ADMIN_PREFIX}/users?search=STAFF").json()["total"] == 1


def test_user_search_matches_the_email_and_the_name(
    people: dict[str, TestClient], db: Session
) -> None:
    make_user(db, "kamal@shop.lk", "customer")
    db.execute(update(User).where(User.email == "kamal@shop.lk").values(name="Someone Else"))

    by_email = people["admin"].get(f"{ADMIN_PREFIX}/users?search=shop.lk").json()
    by_name = people["admin"].get(f"{ADMIN_PREFIX}/users?search=someone").json()

    assert [user["email"] for user in by_email["items"]] == ["kamal@shop.lk"]
    assert [user["email"] for user in by_name["items"]] == ["kamal@shop.lk"]


def test_an_unknown_role_filter_is_rejected(people: dict[str, TestClient]) -> None:
    assert people["admin"].get(f"{ADMIN_PREFIX}/users?role=root").status_code == 422


# ---------- changing roles ----------


def change(browser: TestClient, user_id: int, role: str):
    return browser.patch(
        f"{ADMIN_PREFIX}/users/{user_id}/role", json={"role": role}, headers={"Origin": WEB_ORIGIN}
    )


def user_id(db: Session, email: str) -> int:
    return db.scalar(select(User.id).where(User.email == email))


def test_admin_changes_a_role_and_it_is_audited(people: dict[str, TestClient], db: Session) -> None:
    response = change(people["admin"], user_id(db, "customer@example.com"), "staff")

    assert response.status_code == 200
    assert response.json()["role"] == "staff"
    entry = db.scalars(select(AuditLog)).one()
    assert entry.action == "user.role_changed"
    assert entry.actor_email == "admin@example.com"
    assert entry.details == {"email": "customer@example.com", "from": "customer", "to": "staff"}


def test_a_role_change_signs_the_person_out_everywhere(
    people: dict[str, TestClient], db: Session
) -> None:
    target = user_id(db, "customer@example.com")
    assert people["customer"].get("/api/v1/auth/me").status_code == 200

    change(people["admin"], target, "staff")

    assert people["customer"].get("/api/v1/auth/me").status_code == 401
    assert db.scalars(select(UserSession).where(UserSession.user_id == target)).first() is None


def test_an_admin_cannot_change_their_own_role(people: dict[str, TestClient], db: Session) -> None:
    response = change(people["admin"], user_id(db, "admin@example.com"), "customer")

    assert response.status_code == 409
    assert db.scalar(select(User.role).where(User.email == "admin@example.com")) == "admin"
    assert db.scalars(select(AuditLog)).first() is None


def test_an_admin_cannot_demote_themselves_even_when_another_admin_exists(
    people: dict[str, TestClient], db: Session
) -> None:
    make_user(db, "second@example.com", "admin")

    response = change(people["admin"], user_id(db, "admin@example.com"), "customer")

    assert response.status_code == 409
    assert "own role" in response.json()["detail"]


def test_the_last_admin_cannot_be_demoted(people: dict[str, TestClient], db: Session) -> None:
    second = make_user(db, "second@example.com", "admin")
    first_browser = people["admin"]
    second_browser = signed_in("second@example.com")

    assert change(first_browser, second.id, "customer").status_code == 200
    # Now only the first admin is left. The second was signed out and is a customer, so cannot act,
    # and the first cannot demote themselves, so the store keeps its admin.
    assert change(second_browser, user_id(db, "admin@example.com"), "customer").status_code == 401
    assert change(first_browser, user_id(db, "admin@example.com"), "customer").status_code == 409
    assert db.scalar(select(User.role).where(User.email == "admin@example.com")) == "admin"


def test_the_last_admin_guard_holds_without_the_self_change_rule(
    db: Session, people: dict[str, TestClient]
) -> None:
    from app.services import admin as admin_service

    only_admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    other = make_user(db, "other@example.com", "staff")
    # A second actor who is not an admin in the table cannot exist through the API, so call the
    # service the way a script would: the sole admin is the target and someone else is the actor.
    with pytest.raises(admin_service.AdminError) as failure:
        admin_service.change_role(db, actor=other, user_id=only_admin.id, new_role="staff")
    assert failure.value.status_code == 409
    assert "at least one admin" in failure.value.message


@pytest.mark.parametrize(
    ("target_email", "role", "status"),
    [
        ("customer@example.com", "customer", 409),
        ("customer@example.com", "root", 422),
        ("customer@example.com", "", 422),
    ],
)
def test_bad_role_changes_are_refused(
    people: dict[str, TestClient], db: Session, target_email: str, role: str, status: int
) -> None:
    assert change(people["admin"], user_id(db, target_email), role).status_code == status


def test_changing_the_role_of_a_missing_user_is_a_404(people: dict[str, TestClient]) -> None:
    assert change(people["admin"], 999999, "staff").status_code == 404


def test_extra_fields_in_a_role_change_are_rejected(
    people: dict[str, TestClient], db: Session
) -> None:
    response = people["admin"].patch(
        f"{ADMIN_PREFIX}/users/{user_id(db, 'customer@example.com')}/role",
        json={"role": "staff", "email": "x@example.com"},
        headers={"Origin": WEB_ORIGIN},
    )
    assert response.status_code == 422


# ---------- the audit log ----------


def test_admin_reads_the_audit_log_newest_first(people: dict[str, TestClient], db: Session) -> None:
    target = user_id(db, "customer@example.com")
    change(people["admin"], target, "staff")
    change(people["admin"], target, "customer")

    body = people["admin"].get(f"{ADMIN_PREFIX}/audit-log").json()

    assert body["total"] == 2
    assert [entry["details"]["to"] for entry in body["items"]] == ["customer", "staff"]


def test_audit_entries_cannot_be_updated(people: dict[str, TestClient], db: Session) -> None:
    change(people["admin"], user_id(db, "customer@example.com"), "staff")

    with pytest.raises(DBAPIError, match="cannot be changed"):
        with db.begin_nested():
            db.execute(update(AuditLog).values(action="something.else"))
    with pytest.raises(DBAPIError, match="cannot be changed"):
        with db.begin_nested():
            db.execute(text("UPDATE audit_log SET details = '{}'::json"))


def test_audit_entries_cannot_be_deleted(people: dict[str, TestClient], db: Session) -> None:
    change(people["admin"], user_id(db, "customer@example.com"), "staff")

    with pytest.raises(DBAPIError, match="cannot be deleted"):
        with db.begin_nested():
            db.execute(delete(AuditLog))


def test_deleting_a_user_keeps_their_audit_trail(
    people: dict[str, TestClient], db: Session
) -> None:
    actor = db.scalar(select(User).where(User.email == "admin@example.com"))
    change(people["admin"], user_id(db, "customer@example.com"), "staff")

    db.execute(delete(UserSession).where(UserSession.user_id == actor.id))
    db.delete(actor)
    db.flush()

    entry = db.scalars(select(AuditLog)).one()
    assert entry.actor_id is None
    assert entry.actor_email == "admin@example.com"


def test_secrets_are_scrubbed_from_audit_details(db: Session) -> None:
    entry = audit.record(
        db,
        actor=None,
        action="test.action",
        entity="test",
        entity_id=1,
        details={
            "ok": 1,
            "password": "x",
            "nested": {
                "apiKey": "x",
                "api_key": "x",
                "Authorization": "x",
                "fine": [{"token": "x", "n": 2}],
            },
        },
    )

    assert entry.details == {"ok": 1, "nested": {"fine": [{"n": 2}]}}
    assert entry.actor_email == "system"


# ---------- dashboard ----------


def test_dashboard_counts(people: dict[str, TestClient], catalogue: None) -> None:
    body = people["staff"].get(f"{ADMIN_PREFIX}/dashboard").json()

    assert body["products"] == 17
    assert body["customers"] == 1
    assert body["ordersByStatus"]["pending"] == 0
