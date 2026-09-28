"""The full flow through the real endpoints: setup, confirm, login with a code, recovery codes,
and disabling. tests/test_twofa_service.py checks the building blocks in more detail."""

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.main import app
from tests.test_admin_api import WEB_ORIGIN, make_user, signed_in

TWOFA = "/api/v1/auth/2fa"
LOGIN = "/api/v1/auth/login"
PASSWORD = "sunrise2026"
TEST_KEY = "MzRuJGsBgC9T4CXs2hN9fwVK8LrMOahRjY_Useparjs="


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "totp_encryption_key", TEST_KEY)


@pytest.fixture
def staff(client: TestClient, db: Session) -> TestClient:
    make_user(db, "staffer@example.com", "staff")
    return signed_in("staffer@example.com")


def code_for(secret: str) -> str:
    return pyotp.TOTP(secret).now()


def setup(browser: TestClient) -> str:
    response = browser.post(f"{TWOFA}/setup", headers={"Origin": WEB_ORIGIN})
    assert response.status_code == 200
    return response.json()["secret"]


def confirm(browser: TestClient, secret: str):
    return browser.post(
        f"{TWOFA}/confirm", json={"code": code_for(secret)}, headers={"Origin": WEB_ORIGIN}
    )


def enable(browser: TestClient) -> tuple[str, list[str]]:
    secret = setup(browser)
    response = confirm(browser, secret)
    return secret, response.json()["recoveryCodes"]


def login(client: TestClient, email: str = "staffer@example.com", password: str = PASSWORD):
    return client.post(
        LOGIN, json={"email": email, "password": password}, headers={"Origin": WEB_ORIGIN}
    )


def verify(client: TestClient, pending_token: str, code: str):
    return client.post(
        f"{TWOFA}/verify",
        json={"pendingToken": pending_token, "code": code},
        headers={"Origin": WEB_ORIGIN},
    )


# ---------- setup and confirm ----------


def test_setup_returns_a_secret_and_a_provisioning_uri(staff: TestClient) -> None:
    response = staff.post(f"{TWOFA}/setup", headers={"Origin": WEB_ORIGIN})

    assert response.status_code == 200
    body = response.json()
    assert body["secret"] and body["provisioningUri"].startswith("otpauth://")


def test_setup_is_refused_when_not_configured(
    staff: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "totp_encryption_key", None)

    assert staff.post(f"{TWOFA}/setup", headers={"Origin": WEB_ORIGIN}).status_code == 503


def test_2fa_is_off_until_confirmed(staff: TestClient) -> None:
    setup(staff)

    assert staff.get("/api/v1/auth/me").json()["twoFactorEnabled"] is False


def test_confirming_with_the_right_code_turns_it_on_and_issues_recovery_codes(
    staff: TestClient,
) -> None:
    secret = setup(staff)

    response = confirm(staff, secret)

    assert response.status_code == 200
    codes = response.json()["recoveryCodes"]
    assert len(codes) == settings.recovery_code_count == len(set(codes))
    assert staff.get("/api/v1/auth/me").json()["twoFactorEnabled"] is True


def test_confirming_with_the_wrong_code_does_not_turn_it_on(staff: TestClient) -> None:
    setup(staff)

    response = staff.post(
        f"{TWOFA}/confirm", json={"code": "000000"}, headers={"Origin": WEB_ORIGIN}
    )

    assert response.status_code == 401
    assert staff.get("/api/v1/auth/me").json()["twoFactorEnabled"] is False


def test_confirming_without_setting_up_first_is_refused(staff: TestClient) -> None:
    response = staff.post(
        f"{TWOFA}/confirm", json={"code": "123456"}, headers={"Origin": WEB_ORIGIN}
    )

    assert response.status_code == 409


def test_setup_is_refused_once_already_enabled(staff: TestClient) -> None:
    enable(staff)

    assert staff.post(f"{TWOFA}/setup", headers={"Origin": WEB_ORIGIN}).status_code == 409


def test_confirming_again_once_enabled_is_refused(staff: TestClient) -> None:
    secret, _ = enable(staff)

    assert confirm(staff, secret).status_code == 409


def test_repeated_wrong_confirm_codes_are_locked_out(staff: TestClient) -> None:
    setup(staff)

    for _ in range(settings.twofa_lockout_attempts):
        staff.post(f"{TWOFA}/confirm", json={"code": "000000"}, headers={"Origin": WEB_ORIGIN})

    response = staff.post(
        f"{TWOFA}/confirm", json={"code": "000000"}, headers={"Origin": WEB_ORIGIN}
    )
    assert response.status_code == 429


# ---------- login with a code ----------


def test_login_needs_a_second_step_once_2fa_is_on(staff: TestClient, db: Session) -> None:
    enable(staff)
    fresh = TestClient(app)

    response = login(fresh)

    assert response.status_code == 200
    body = response.json()
    assert body["twoFactorRequired"] is True
    assert body["pendingToken"]
    assert "set-cookie" not in response.headers
    assert fresh.get("/api/v1/auth/me").status_code == 401


def test_the_right_code_completes_the_sign_in(staff: TestClient) -> None:
    secret, _ = enable(staff)
    fresh = TestClient(app)
    pending = login(fresh).json()["pendingToken"]

    response = verify(fresh, pending, code_for(secret))

    assert response.status_code == 200
    assert response.json()["email"] == "staffer@example.com"
    assert "set-cookie" in response.headers
    assert fresh.get("/api/v1/auth/me").status_code == 200


def test_a_recovery_code_also_completes_the_sign_in(staff: TestClient) -> None:
    _, codes = enable(staff)
    fresh = TestClient(app)
    pending = login(fresh).json()["pendingToken"]

    response = verify(fresh, pending, codes[0])

    assert response.status_code == 200
    assert "set-cookie" in response.headers


def test_a_used_recovery_code_cannot_be_used_again(staff: TestClient) -> None:
    _, codes = enable(staff)
    fresh = TestClient(app)
    verify(fresh, login(fresh).json()["pendingToken"], codes[0])

    second = TestClient(app)
    response = verify(second, login(second).json()["pendingToken"], codes[0])

    assert response.status_code == 401


def test_the_wrong_code_does_not_sign_in(staff: TestClient) -> None:
    enable(staff)
    fresh = TestClient(app)
    pending = login(fresh).json()["pendingToken"]

    response = verify(fresh, pending, "000000")

    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_a_pending_token_can_only_be_used_once(staff: TestClient) -> None:
    secret, _ = enable(staff)
    fresh = TestClient(app)
    pending = login(fresh).json()["pendingToken"]
    verify(fresh, pending, code_for(secret))

    second = TestClient(app)
    response = verify(second, pending, code_for(secret))

    assert response.status_code == 401


def test_an_unknown_pending_token_is_refused(staff: TestClient) -> None:
    response = verify(TestClient(app), "not-a-real-token", "123456")

    assert response.status_code == 401


def test_repeated_wrong_codes_at_login_are_locked_out(staff: TestClient) -> None:
    enable(staff)
    fresh = TestClient(app)
    pending = login(fresh).json()["pendingToken"]

    for _ in range(settings.twofa_lockout_attempts):
        verify(fresh, pending, "000000")

    response = verify(fresh, pending, "000000")
    assert response.status_code == 429


def test_a_customer_login_is_unaffected(client: TestClient, db: Session) -> None:
    from tests.helpers import sign_up

    sign_up(client, email="shopper@example.com")

    response = login(client, email="shopper@example.com", password="sunrise2026")

    assert response.status_code == 200
    assert "twoFactorRequired" not in response.json()


# ---------- disabling ----------


def test_disabling_needs_the_password_and_a_valid_code(staff: TestClient) -> None:
    secret, _ = enable(staff)

    response = staff.post(
        f"{TWOFA}/disable",
        json={"password": PASSWORD, "code": code_for(secret)},
        headers={"Origin": WEB_ORIGIN},
    )

    assert response.status_code == 204
    assert staff.get("/api/v1/auth/me").json()["twoFactorEnabled"] is False


def test_disabling_with_the_wrong_password_is_refused(staff: TestClient) -> None:
    secret, _ = enable(staff)

    response = staff.post(
        f"{TWOFA}/disable",
        json={"password": "wrong-password-1", "code": code_for(secret)},
        headers={"Origin": WEB_ORIGIN},
    )

    assert response.status_code == 401
    assert staff.get("/api/v1/auth/me").json()["twoFactorEnabled"] is True


def test_disabling_with_the_wrong_code_is_refused(staff: TestClient) -> None:
    enable(staff)

    response = staff.post(
        f"{TWOFA}/disable",
        json={"password": PASSWORD, "code": "000000"},
        headers={"Origin": WEB_ORIGIN},
    )

    assert response.status_code == 401
    assert staff.get("/api/v1/auth/me").json()["twoFactorEnabled"] is True


def test_disabling_a_recovery_code_also_works(staff: TestClient) -> None:
    _, codes = enable(staff)

    response = staff.post(
        f"{TWOFA}/disable",
        json={"password": PASSWORD, "code": codes[0]},
        headers={"Origin": WEB_ORIGIN},
    )

    assert response.status_code == 204


def test_disabling_when_not_enabled_is_refused(staff: TestClient) -> None:
    response = staff.post(
        f"{TWOFA}/disable",
        json={"password": PASSWORD, "code": "000000"},
        headers={"Origin": WEB_ORIGIN},
    )

    assert response.status_code == 409


def test_after_disabling_login_no_longer_needs_a_code(staff: TestClient) -> None:
    secret, _ = enable(staff)
    staff.post(
        f"{TWOFA}/disable",
        json={"password": PASSWORD, "code": code_for(secret)},
        headers={"Origin": WEB_ORIGIN},
    )
    fresh = TestClient(app)

    response = login(fresh)

    assert response.status_code == 200
    assert "twoFactorRequired" not in response.json()


def test_disabling_leaves_the_current_session_signed_in(staff: TestClient) -> None:
    secret, _ = enable(staff)

    staff.post(
        f"{TWOFA}/disable",
        json={"password": PASSWORD, "code": code_for(secret)},
        headers={"Origin": WEB_ORIGIN},
    )

    assert staff.get("/api/v1/auth/me").status_code == 200


# ---------- origin check ----------


def test_every_2fa_route_rejects_an_untrusted_origin(staff: TestClient) -> None:
    for path in ("setup", "confirm", "disable", "verify"):
        response = staff.post(
            f"{TWOFA}/{path}", json={}, headers={"Origin": "https://evil.example"}
        )
        assert response.status_code == 403, path
