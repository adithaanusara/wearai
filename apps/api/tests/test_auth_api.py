import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import security
from app.config import settings
from app.main import app
from app.models import User, UserSession

EMAIL = "nimali@example.com"
PASSWORD = "sunrise2026"
WEB_ORIGIN = "http://localhost:3000"


def register(client: TestClient, **overrides):
    body = {"name": "Nimali Perera", "email": EMAIL, "password": PASSWORD, **overrides}
    return client.post("/api/v1/auth/register", json=body)


def login(client: TestClient, email: str = EMAIL, password: str = PASSWORD, **kwargs):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}, **kwargs)


def sessions(db: Session) -> list[UserSession]:
    return list(db.scalars(select(UserSession)))


# ---------- register ----------


def test_register_creates_the_account_and_signs_in(client: TestClient) -> None:
    response = register(client)

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "name": "Nimali Perera",
        "email": EMAIL,
        "role": "customer",
    }
    assert client.get("/api/v1/auth/me").json()["email"] == EMAIL


def test_responses_never_contain_the_password_or_its_hash(client: TestClient) -> None:
    text = register(client).text + client.get("/api/v1/auth/me").text

    assert PASSWORD not in text
    assert "argon2" not in text
    assert "password" not in text.lower()


def test_password_is_stored_only_as_an_argon2id_hash(client: TestClient, db: Session) -> None:
    register(client)

    user = db.scalars(select(User)).one()
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash
    assert security.verify_password(user.password_hash, PASSWORD)


def test_email_is_trimmed_and_lowercased(client: TestClient, db: Session) -> None:
    response = register(client, email="  Nimali@Example.COM ")

    assert response.json()["email"] == EMAIL
    assert db.scalars(select(User)).one().email == EMAIL


def test_duplicate_email_is_rejected_regardless_of_case(client: TestClient, db: Session) -> None:
    register(client)

    response = register(client, email="NIMALI@example.com", name="Someone Else")

    assert response.status_code == 409
    assert response.json() == {"detail": "An account with this email already exists"}
    assert len(db.scalars(select(User)).all()) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short1"},
        {"password": "abcdefgh"},
        {"password": "12345678"},
        {"password": "a1" * 64 + "x"},
        {"name": "   "},
        {"name": "x" * 121},
        {"email": "not-an-email"},
        {"email": ""},
    ],
    ids=[
        "short password",
        "no digit",
        "no letter",
        "too long",
        "blank name",
        "long name",
        "bad email",
        "empty email",
    ],
)
def test_invalid_registration_is_rejected_without_creating_a_user(
    client: TestClient, db: Session, overrides: dict
) -> None:
    response = register(client, **overrides)

    assert response.status_code == 422
    assert db.scalars(select(User)).all() == []
    assert "sessions" not in response.headers.get("set-cookie", "")


def test_a_validation_error_does_not_echo_the_submitted_password(client: TestClient) -> None:
    response = register(client, password="short1")

    assert response.status_code == 422
    assert "short1" not in response.text
    assert all("input" not in problem for problem in response.json()["detail"])
    assert response.json()["detail"][0]["msg"] == "Use at least 8 characters."


def test_the_longest_allowed_password_works(client: TestClient) -> None:
    long_password = "a1" * 64

    assert register(client, password=long_password).status_code == 201
    assert login(client, password=long_password).status_code == 200


def test_missing_fields_are_rejected(client: TestClient) -> None:
    assert client.post("/api/v1/auth/register", json={}).status_code == 422
    assert client.post("/api/v1/auth/register", content=b"not json").status_code == 422


# ---------- cookie and session storage ----------


def test_session_cookie_is_httponly_lax_and_expires_in_two_weeks(client: TestClient) -> None:
    cookie = register(client).headers["set-cookie"].lower()

    assert cookie.startswith(f"{settings.session_cookie_name}=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert f"max-age={14 * 24 * 60 * 60}" in cookie
    assert "secure" not in cookie  # off by default so local http works


def test_cookie_is_secure_when_configured_for_production(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "cookie_secure", True)

    cookie = register(client).headers["set-cookie"].lower()

    assert "secure" in cookie


def test_only_the_hash_of_the_token_is_stored(client: TestClient, db: Session) -> None:
    register(client)
    token = client.cookies.get(settings.session_cookie_name)

    stored = sessions(db)
    assert len(stored) == 1
    assert token and token != stored[0].id
    assert stored[0].id == hashlib.sha256(token.encode()).hexdigest()


def test_session_is_valid_for_about_fourteen_days(client: TestClient, db: Session) -> None:
    register(client)

    remaining = sessions(db)[0].expires_at - datetime.now(UTC)
    assert timedelta(days=13, hours=23) < remaining <= timedelta(days=14)


# ---------- login ----------


def test_login_succeeds_with_any_capitalisation_of_the_email(client: TestClient) -> None:
    register(client)
    fresh = TestClient(app)

    response = login(fresh, email="NIMALI@Example.com")

    assert response.status_code == 200
    assert response.json()["name"] == "Nimali Perera"
    assert fresh.get("/api/v1/auth/me").status_code == 200


def test_wrong_password_and_unknown_email_look_identical(client: TestClient) -> None:
    register(client)
    fresh = TestClient(app)

    wrong_password = login(fresh, password="wrongpass1")
    unknown_email = login(fresh, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {"detail": "Invalid email or password"}
    assert "set-cookie" not in wrong_password.headers
    assert "set-cookie" not in unknown_email.headers


def test_an_unknown_email_still_costs_a_password_verification(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(security, "verify_dummy", lambda password: calls.append(password))

    login(client, email="nobody@example.com")

    assert calls == [PASSWORD]  # so a missing account cannot be spotted by timing


def test_an_empty_login_password_gets_a_readable_message(client: TestClient) -> None:
    problem = login(client, password="").json()["detail"][0]

    assert problem["loc"] == ["body", "password"]
    assert problem["msg"] == "This field is required."


def test_login_rejects_bad_input(client: TestClient) -> None:
    assert login(client, email="not-an-email").status_code == 422
    assert login(client, password="").status_code == 422
    assert login(client, password="x" * 129).status_code == 422


def test_login_issues_a_new_session_and_retires_the_old_one(
    client: TestClient, db: Session
) -> None:
    register(client)
    old_token = client.cookies.get(settings.session_cookie_name)

    login(client)
    new_token = client.cookies.get(settings.session_cookie_name)

    assert new_token != old_token
    assert len(sessions(db)) == 1
    stale = TestClient(app)
    stale.cookies.set(settings.session_cookie_name, old_token)
    assert stale.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 200


def test_an_old_weaker_hash_is_upgraded_on_login(client: TestClient, db: Session) -> None:
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(PASSWORD)
    db.add(User(email=EMAIL, name="Nimali", password_hash=weak))
    db.commit()

    assert login(client).status_code == 200

    upgraded = db.scalars(select(User)).one().password_hash
    assert upgraded != weak
    assert not security.needs_rehash(upgraded)


# ---------- me ----------


def test_me_requires_a_session(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("cookie", ["garbage", "", "a" * 500, "' OR 1=1 --"])
def test_me_rejects_forged_or_tampered_cookies(client: TestClient, cookie: str) -> None:
    register(client)
    forged = TestClient(app)
    forged.cookies.set(settings.session_cookie_name, cookie)

    assert forged.get("/api/v1/auth/me").status_code == 401


def test_tampering_with_a_real_token_invalidates_it(client: TestClient) -> None:
    register(client)
    token = client.cookies.get(settings.session_cookie_name)
    tampered = TestClient(app)
    tampered.cookies.set(
        settings.session_cookie_name, token[:-1] + ("A" if token[-1] != "A" else "B")
    )

    assert tampered.get("/api/v1/auth/me").status_code == 401


def test_an_expired_session_is_rejected_and_removed(client: TestClient, db: Session) -> None:
    register(client)
    db.execute(update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(minutes=1)))
    db.commit()

    assert client.get("/api/v1/auth/me").status_code == 401
    assert sessions(db) == []


def test_auth_responses_are_not_cacheable(client: TestClient) -> None:
    registered = register(client)
    me = client.get("/api/v1/auth/me")

    assert registered.headers["cache-control"] == "no-store"
    assert me.headers["cache-control"] == "no-store"


# ---------- session (the website's "is anyone signed in?" question) ----------


def test_a_visitor_gets_a_normal_answer_with_no_user(client: TestClient) -> None:
    response = client.get("/api/v1/auth/session")

    assert response.status_code == 200
    assert response.json() == {"user": None}
    assert response.headers["cache-control"] == "no-store"


def test_a_signed_in_visitor_gets_their_user(client: TestClient) -> None:
    register(client)

    body = client.get("/api/v1/auth/session").json()

    assert body["user"] == {
        "id": body["user"]["id"],
        "name": "Nimali Perera",
        "email": EMAIL,
        "role": "customer",
    }
    assert "password" not in str(body).lower()


@pytest.mark.parametrize("cookie", ["garbage", "a" * 500, "' OR 1=1 --"])
def test_a_forged_cookie_looks_like_a_visitor(client: TestClient, cookie: str) -> None:
    forged = TestClient(app)
    forged.cookies.set(settings.session_cookie_name, cookie)

    assert forged.get("/api/v1/auth/session").json() == {"user": None}


def test_an_expired_session_looks_like_a_visitor(client: TestClient, db: Session) -> None:
    register(client)
    db.execute(update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(minutes=1)))
    db.commit()

    assert client.get("/api/v1/auth/session").json() == {"user": None}
    assert sessions(db) == []


def test_after_logout_the_session_is_empty(client: TestClient) -> None:
    register(client)
    client.post("/api/v1/auth/logout")

    assert client.get("/api/v1/auth/session").json() == {"user": None}


# ---------- logout ----------


def test_logout_ends_the_session_and_clears_the_cookie(client: TestClient, db: Session) -> None:
    register(client)

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert sessions(db) == []
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_without_a_session_is_harmless(client: TestClient) -> None:
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_logout_only_ends_the_callers_own_session(client: TestClient, db: Session) -> None:
    register(client)
    other = TestClient(app)
    login(other)

    client.post("/api/v1/auth/logout")

    assert other.get("/api/v1/auth/me").status_code == 200
    assert len(sessions(db)) == 1


def test_deleting_a_user_removes_their_sessions(client: TestClient, db: Session) -> None:
    register(client)

    db.delete(db.scalars(select(User)).one())
    db.commit()

    assert sessions(db) == []


# ---------- CSRF: origin check and CORS ----------


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://localhost:3001"])
def test_posts_from_untrusted_origins_are_rejected(client: TestClient, origin: str) -> None:
    register(client)
    fresh = TestClient(app)

    response = login(fresh, headers={"Origin": origin})

    assert response.status_code == 403
    assert "set-cookie" not in response.headers


def test_a_forged_registration_creates_nothing(client: TestClient, db: Session) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Eve", "email": "eve@example.com", "password": PASSWORD},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert db.scalars(select(User)).all() == []


def test_a_forged_logout_leaves_the_session_alone(client: TestClient) -> None:
    register(client)

    response = client.post("/api/v1/auth/logout", headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 200


def test_the_website_origin_and_originless_requests_are_allowed(client: TestClient) -> None:
    register(client)

    assert login(TestClient(app), headers={"Origin": WEB_ORIGIN}).status_code == 200
    assert login(TestClient(app)).status_code == 200


def test_cors_allows_credentials_only_for_the_website(client: TestClient) -> None:
    allowed = client.get("/api/v1/health", headers={"Origin": WEB_ORIGIN})
    denied = client.get("/api/v1/health", headers={"Origin": "https://evil.example"})

    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-origin" not in denied.headers
