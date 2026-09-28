"""The lockout and rate limits as a browser would actually hit them, through /auth/login and
/auth/register. tests/test_login_limits.py checks the underlying rules in more detail."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.main import app
from tests.helpers import sign_up
from tests.test_auth_api import EMAIL, WEB_ORIGIN, login, register


def client_at(ip: str, port: int = 1) -> TestClient:
    return TestClient(app, client=(ip, port))


def bad_login(client: TestClient, email: str = EMAIL):
    return login(client, email=email, password="wrong-password", headers={"Origin": WEB_ORIGIN})


# ---------- account lockout ----------


def test_the_account_locks_after_enough_wrong_passwords(client: TestClient) -> None:
    register(client)

    for _ in range(settings.login_lockout_attempts):
        assert bad_login(client_at("1.1.1.1")).status_code == 401

    locked = bad_login(client_at("2.2.2.2"))  # a different address: still the same account
    assert locked.status_code == 429
    assert locked.json()["detail"]["code"] == "too_many_attempts"
    assert "retry-after" in {h.lower() for h in locked.headers}


def test_a_locked_account_is_refused_even_with_the_right_password(client: TestClient) -> None:
    register(client)
    for _ in range(settings.login_lockout_attempts):
        bad_login(client_at("1.1.1.1"))

    response = login(client_at("3.3.3.3"), headers={"Origin": WEB_ORIGIN})

    assert response.status_code == 429
    assert "set-cookie" not in response.headers


def test_the_lockout_message_does_not_say_which_check_failed(client: TestClient) -> None:
    register(client)
    for _ in range(settings.login_lockout_attempts):
        bad_login(client_at("1.1.1.1"))

    body = bad_login(client_at("1.1.1.1")).json()

    assert body["detail"]["message"] == "Too many attempts. Please try again later."
    assert "lock" not in body["detail"]["message"].lower()
    assert "ip" not in body["detail"]["message"].lower()
    assert "address" not in body["detail"]["message"].lower()


def test_a_successful_login_lets_later_wrong_passwords_start_counting_again(
    client: TestClient,
) -> None:
    register(client)
    for _ in range(settings.login_lockout_attempts - 1):
        bad_login(client_at("1.1.1.1"))
    assert login(client_at("1.1.1.1"), headers={"Origin": WEB_ORIGIN}).status_code == 200

    for _ in range(settings.login_lockout_attempts - 1):
        assert bad_login(client_at("1.1.1.1")).status_code == 401
    # one more below the limit again, thanks to the reset
    assert login(client_at("1.1.1.1"), headers={"Origin": WEB_ORIGIN}).status_code == 200


def test_locking_one_account_does_not_affect_another(client: TestClient, db: Session) -> None:
    register(client)
    sign_up(client, email="second@example.com")
    for _ in range(settings.login_lockout_attempts):
        bad_login(client_at("1.1.1.1"))

    response = login(
        client_at("1.1.1.1"), email="second@example.com", headers={"Origin": WEB_ORIGIN}
    )

    assert response.status_code == 200


# ---------- per-address rate limit ----------


def test_the_address_is_rate_limited_across_different_accounts(client: TestClient) -> None:
    register(client)
    fixed_ip = client_at("9.9.9.9")
    for i in range(settings.login_ip_rate_limit_requests):
        bad_login(fixed_ip, email=f"nobody-{i}@example.com")

    response = bad_login(fixed_ip, email="yet-another@example.com")

    assert response.status_code == 429


def test_a_different_address_is_not_affected(client: TestClient) -> None:
    register(client)
    for i in range(settings.login_ip_rate_limit_requests):
        bad_login(client_at("9.9.9.9"), email=f"nobody-{i}@example.com")

    response = login(client_at("8.8.8.8"), headers={"Origin": WEB_ORIGIN})

    assert response.status_code == 200


# ---------- registration ----------


def test_registration_is_rate_limited_by_address(client: TestClient) -> None:
    fixed_ip = client_at("5.5.5.5")
    for i in range(settings.register_ip_rate_limit_requests):
        assert register(fixed_ip, email=f"person-{i}@example.com").status_code == 201

    response = register(fixed_ip, email="one-more@example.com")

    assert response.status_code == 429
    assert "retry-after" in {h.lower() for h in response.headers}


def test_a_taken_email_still_counts_towards_the_registration_limit(client: TestClient) -> None:
    fixed_ip = client_at("6.6.6.6")
    register(fixed_ip)
    for _ in range(settings.register_ip_rate_limit_requests - 1):
        assert register(fixed_ip).status_code == 409  # the same, already-taken email

    response = register(fixed_ip)

    assert response.status_code == 429


def test_a_different_address_can_still_register(client: TestClient) -> None:
    fixed_ip = client_at("5.5.5.5")
    for i in range(settings.register_ip_rate_limit_requests):
        register(fixed_ip, email=f"person-{i}@example.com")

    response = register(client_at("7.7.7.7"), email="new-person@example.com")

    assert response.status_code == 201


def test_registering_does_not_count_towards_the_login_rate_limit(client: TestClient) -> None:
    fixed_ip = client_at("4.4.4.4")
    for i in range(settings.login_ip_rate_limit_requests):
        register(fixed_ip, email=f"person-{i}@example.com")

    response = login(fixed_ip, email="person-0@example.com", headers={"Origin": WEB_ORIGIN})

    assert response.status_code == 200
