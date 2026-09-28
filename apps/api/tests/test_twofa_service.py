"""The pure 2FA building blocks, apart from the API."""

from datetime import UTC, datetime

import pyotp
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import security
from app.config import settings
from app.models import PendingLogin, RecoveryCode, User
from app.services import twofa

TEST_KEY = "MzRuJGsBgC9T4CXs2hN9fwVK8LrMOahRjY_Useparjs="


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "totp_encryption_key", TEST_KEY)


@pytest.fixture
def user(db: Session) -> User:
    created = User(name="Staffer", email="staffer@example.com", password_hash="x", role="staff")
    db.add(created)
    db.flush()
    return created


def current_code(secret: str) -> str:
    # `verify_totp` allows the current and the adjacent 30-second step either side, so computing
    # the code for "now" here and checking it a moment later is not a race: real clock drift
    # between an authenticator app and this server is exactly what that allowance is for.
    return pyotp.TOTP(secret).now()


# ---------- configuration ----------


def test_is_configured_follows_the_encryption_key(monkeypatch: pytest.MonkeyPatch) -> None:
    assert twofa.is_configured()
    monkeypatch.setattr(settings, "totp_encryption_key", None)
    assert not twofa.is_configured()


def test_setup_is_refused_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "totp_encryption_key", None)
    with pytest.raises(twofa.NotConfiguredError):
        twofa.encrypt_secret("anything")


# ---------- secrets and codes ----------


def test_a_freshly_generated_secret_verifies_its_own_current_code() -> None:
    secret = twofa.generate_secret()
    assert twofa.verify_totp(secret, current_code(secret))


def test_the_wrong_code_is_refused() -> None:
    secret = twofa.generate_secret()
    assert not twofa.verify_totp(secret, "000000")


def test_a_code_from_a_different_secret_is_refused() -> None:
    a, b = twofa.generate_secret(), twofa.generate_secret()
    assert not twofa.verify_totp(a, current_code(b))


def test_the_provisioning_uri_names_the_account_and_the_store() -> None:
    secret = twofa.generate_secret()
    uri = twofa.provisioning_uri(secret, "staffer@example.com")

    assert uri.startswith("otpauth://totp/")
    assert "staffer%40example.com" in uri
    assert f"issuer={settings.store_name}" in uri
    assert secret in uri


# ---------- encryption at rest ----------


def test_encrypting_and_decrypting_returns_the_original_secret() -> None:
    secret = twofa.generate_secret()

    encrypted = twofa.encrypt_secret(secret)

    assert secret not in encrypted
    assert twofa.decrypt_secret(encrypted) == secret


def test_decrypting_with_the_wrong_key_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    encrypted = twofa.encrypt_secret(twofa.generate_secret())

    monkeypatch.setattr(settings, "totp_encryption_key", "x" * 43 + "=")
    assert twofa.decrypt_secret(encrypted) is None


def test_decrypting_nonsense_fails_safely() -> None:
    assert twofa.decrypt_secret("not-a-real-token") is None


# ---------- recovery codes ----------


def test_ten_distinct_recovery_codes_are_generated(db: Session, user: User) -> None:
    codes = twofa.generate_recovery_codes(db, user)

    assert len(codes) == settings.recovery_code_count == len(set(codes))
    assert db.scalar(select(RecoveryCode).where(RecoveryCode.user_id == user.id)) is not None


def test_a_recovery_code_can_be_used_exactly_once(db: Session, user: User) -> None:
    codes = twofa.generate_recovery_codes(db, user)
    db.commit()

    assert twofa.consume_recovery_code(db, user, codes[0])
    db.commit()
    assert not twofa.consume_recovery_code(db, user, codes[0])


def test_an_unknown_recovery_code_is_refused(db: Session, user: User) -> None:
    twofa.generate_recovery_codes(db, user)
    db.commit()

    assert not twofa.consume_recovery_code(db, user, "AAAA-1111")


def test_generating_again_replaces_the_old_codes(db: Session, user: User) -> None:
    first = twofa.generate_recovery_codes(db, user)
    db.commit()

    second = twofa.generate_recovery_codes(db, user)
    db.commit()

    assert not twofa.consume_recovery_code(db, user, first[0])
    assert twofa.consume_recovery_code(db, user, second[0])


def test_one_users_recovery_code_does_not_work_for_another(db: Session, user: User) -> None:
    other = User(name="Other", email="other@example.com", password_hash="x", role="staff")
    db.add(other)
    db.flush()
    codes = twofa.generate_recovery_codes(db, user)
    db.commit()

    assert not twofa.consume_recovery_code(db, other, codes[0])


# ---------- pending logins ----------


def test_a_pending_login_resolves_to_its_user(db: Session, user: User) -> None:
    token = twofa.start_pending_login(db, user)

    assert twofa.user_for_pending_login(db, token).id == user.id


def test_an_unknown_token_resolves_to_nothing(db: Session) -> None:
    assert twofa.user_for_pending_login(db, "not-a-real-token") is None


def test_an_expired_pending_login_is_refused_and_removed(db: Session, user: User) -> None:
    token = twofa.start_pending_login(db, user)
    row = db.get(PendingLogin, security.hash_token(token))
    row.expires_at = datetime.now(UTC).replace(year=2000)
    db.commit()

    assert twofa.user_for_pending_login(db, token) is None
    assert db.get(PendingLogin, row.id) is None


def test_ending_a_pending_login_makes_it_unusable(db: Session, user: User) -> None:
    token = twofa.start_pending_login(db, user)

    twofa.end_pending_login(db, token)

    assert twofa.user_for_pending_login(db, token) is None


def test_starting_a_new_pending_login_replaces_the_old_one(db: Session, user: User) -> None:
    first = twofa.start_pending_login(db, user)

    second = twofa.start_pending_login(db, user)

    assert twofa.user_for_pending_login(db, first) is None
    assert twofa.user_for_pending_login(db, second).id == user.id


# ---------- disabling ----------


def test_disabling_clears_the_secret_and_every_recovery_code(db: Session, user: User) -> None:
    twofa.generate_recovery_codes(db, user)
    user.totp_secret_encrypted = twofa.encrypt_secret(twofa.generate_secret())
    user.totp_confirmed_at = datetime.now(UTC)
    db.commit()

    twofa.disable(db, user)
    db.commit()

    assert not twofa.is_enabled(user)
    assert user.totp_secret_encrypted is None
    assert db.scalar(select(RecoveryCode).where(RecoveryCode.user_id == user.id)) is None
