"""Unit tests for the limits themselves: exact boundaries, the rolling window, and the reset on a
success. tests/test_login_limits_api.py checks the same rules through the real endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuthAttempt
from app.services.login_limits import (
    TooManyAttemptsError,
    check_login_allowed,
    check_register_allowed,
    record_attempt,
)


def add(
    db: Session, *, kind: str, email: str, ip: str, succeeded: bool, ago_seconds: float
) -> None:
    db.add(
        AuthAttempt(
            kind=kind,
            email=email,
            ip_hash=ip,
            succeeded=succeeded,
            created_at=datetime.now(UTC) - timedelta(seconds=ago_seconds),
        )
    )
    db.commit()


# ---------- per-account lockout ----------


def test_the_account_is_not_locked_below_the_threshold(db: Session) -> None:
    for _ in range(settings.login_lockout_attempts - 1):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=1)

    check_login_allowed(db, email="a@example.com", ip="ip-2")  # a different address: no problem


def test_the_account_is_locked_at_the_threshold(db: Session) -> None:
    for _ in range(settings.login_lockout_attempts):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=1)

    with pytest.raises(TooManyAttemptsError):
        check_login_allowed(db, email="a@example.com", ip="ip-2")


def test_a_success_resets_the_count_even_with_earlier_failures(db: Session) -> None:
    for _ in range(settings.login_lockout_attempts - 1):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=100)
    add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=True, ago_seconds=50)
    for _ in range(settings.login_lockout_attempts - 1):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=1)

    check_login_allowed(db, email="a@example.com", ip="ip-2")  # one below the limit since the reset


def test_a_failure_that_has_aged_out_of_the_window_no_longer_counts(db: Session) -> None:
    stale = settings.login_lockout_window_seconds + 5
    for _ in range(settings.login_lockout_attempts):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=stale)

    check_login_allowed(db, email="a@example.com", ip="ip-2")


def test_two_accounts_never_lock_each_other_out(db: Session) -> None:
    for _ in range(settings.login_lockout_attempts):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=1)

    check_login_allowed(db, email="b@example.com", ip="ip-2")


def test_the_retry_after_matches_when_the_oldest_counted_failure_ages_out(db: Session) -> None:
    add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=200)
    for _ in range(settings.login_lockout_attempts - 1):
        add(db, kind="login", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=1)

    with pytest.raises(TooManyAttemptsError) as failure:
        check_login_allowed(db, email="a@example.com", ip="ip-2")

    expected = settings.login_lockout_window_seconds - 200
    assert expected - 1 <= failure.value.retry_after <= expected + 1


# ---------- per-address rate limit (login) ----------


def test_the_address_is_not_limited_below_the_threshold(db: Session) -> None:
    for _ in range(settings.login_ip_rate_limit_requests - 1):
        add(db, kind="login", email="anyone@example.com", ip="ip-1", succeeded=True, ago_seconds=1)

    check_login_allowed(db, email="new@example.com", ip="ip-1")


def test_the_address_is_limited_at_the_threshold_across_different_accounts(db: Session) -> None:
    for i in range(settings.login_ip_rate_limit_requests):
        add(
            db,
            kind="login",
            email=f"account-{i}@example.com",
            ip="ip-1",
            succeeded=False,
            ago_seconds=1,
        )

    with pytest.raises(TooManyAttemptsError):
        check_login_allowed(db, email="yet-another@example.com", ip="ip-1")


def test_two_addresses_never_limit_each_other(db: Session) -> None:
    for i in range(settings.login_ip_rate_limit_requests):
        add(
            db,
            kind="login",
            email=f"other-{i}@example.com",
            ip="ip-1",
            succeeded=False,
            ago_seconds=1,
        )

    check_login_allowed(db, email="unrelated@example.com", ip="ip-2")


def test_the_ip_limit_counts_successes_too(db: Session) -> None:
    for i in range(settings.login_ip_rate_limit_requests):
        add(
            db,
            kind="login",
            email=f"account-{i}@example.com",
            ip="ip-1",
            succeeded=True,
            ago_seconds=1,
        )

    with pytest.raises(TooManyAttemptsError):
        check_login_allowed(db, email="new@example.com", ip="ip-1")


def test_a_registration_attempt_does_not_count_towards_a_login_lockout(db: Session) -> None:
    for _ in range(settings.login_lockout_attempts):
        add(db, kind="register", email="a@example.com", ip="ip-1", succeeded=False, ago_seconds=1)

    check_login_allowed(db, email="a@example.com", ip="ip-2")


def test_login_and_register_attempts_are_counted_separately(db: Session) -> None:
    for i in range(settings.login_ip_rate_limit_requests):
        add(
            db,
            kind="register",
            email=f"account-{i}@example.com",
            ip="ip-1",
            succeeded=True,
            ago_seconds=1,
        )

    check_login_allowed(db, email="new@example.com", ip="ip-1")


# ---------- registration ----------


def test_registration_is_not_limited_below_the_threshold(db: Session) -> None:
    for _ in range(settings.register_ip_rate_limit_requests - 1):
        add(db, kind="register", email="x@example.com", ip="ip-1", succeeded=True, ago_seconds=1)

    check_register_allowed(db, ip="ip-1")


def test_registration_is_limited_at_the_threshold(db: Session) -> None:
    for _ in range(settings.register_ip_rate_limit_requests):
        add(db, kind="register", email="x@example.com", ip="ip-1", succeeded=True, ago_seconds=1)

    with pytest.raises(TooManyAttemptsError):
        check_register_allowed(db, ip="ip-1")


def test_registration_and_login_from_the_same_address_do_not_share_a_limit(db: Session) -> None:
    for _ in range(settings.login_ip_rate_limit_requests):
        add(db, kind="login", email="x@example.com", ip="ip-1", succeeded=True, ago_seconds=1)

    check_register_allowed(db, ip="ip-1")


# ---------- recording and pruning ----------


def test_record_attempt_writes_no_password_or_raw_address(db: Session) -> None:
    record_attempt(
        db, kind="login", email="a@example.com", ip="a-hash-not-an-address", succeeded=False
    )

    row = db.scalars(select(AuthAttempt)).one()
    assert row.ip_hash == "a-hash-not-an-address"
    assert not hasattr(row, "password")


def test_record_attempt_prunes_very_old_rows(db: Session) -> None:
    add(
        db,
        kind="login",
        email="old@example.com",
        ip="ip-1",
        succeeded=False,
        ago_seconds=60 * 60 * 24,
    )

    record_attempt(db, kind="login", email="new@example.com", ip="ip-1", succeeded=True)

    remaining = db.scalars(select(AuthAttempt.email)).all()
    assert remaining == ["new@example.com"]
