"""Login and registration protection: a per-account lockout and a per-address rate limit.

Both are rolling windows, like the chat assistant's rate limit, and both are checked before the
password is looked at, so a locked-out account and a wrong password look identical from outside.
The message never says which of the two limits (if either) is the reason.
"""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuthAttempt

# Rows older than every window this module checks are pruned on each write, so the table never
# grows without bound. Comfortably longer than the longest window in use.
_RETENTION = timedelta(hours=6)


class TooManyAttemptsError(Exception):
    """Too many recent attempts, from this account or this address. Never says which."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("too many attempts")
        self.retry_after = retry_after


def _now() -> datetime:
    return datetime.now(UTC)


def ip_hash(request: Request) -> str:
    """A salted hash of the caller's address, never the address itself.

    Behind a proxy, configure the server to pass the real client address on (for example
    uvicorn --proxy-headers), or every caller behind it is counted as one.
    """
    address = request.client.host if request.client else "unknown"
    return hmac.new(settings.login_hash_salt.encode(), address.encode(), hashlib.sha256).hexdigest()


def _retry_after(oldest_in_window: datetime, window_seconds: int, now: datetime) -> int:
    wait = (oldest_in_window + timedelta(seconds=window_seconds) - now).total_seconds()
    return max(1, int(wait) + 1)


def _consecutive_failures_since_last_success(
    db: Session, email: str, window_start: datetime
) -> list[datetime]:
    """Failed attempts for this email, newest first, stopping at the most recent success.

    A success needs nothing else to "reset the count": once one is reached, nothing before it is
    ever counted again.
    """
    recent = db.scalars(
        select(AuthAttempt)
        .where(
            AuthAttempt.kind == "login",
            AuthAttempt.email == email,
            AuthAttempt.created_at > window_start,
        )
        .order_by(AuthAttempt.created_at.desc())
    )
    failures: list[datetime] = []
    for attempt in recent:
        if attempt.succeeded:
            break
        failures.append(attempt.created_at)
    return failures


def check_login_allowed(db: Session, *, email: str, ip: str) -> None:
    """Raises `TooManyAttemptsError` if this account or this address should not try again yet."""
    now = _now()

    ip_window_start = now - timedelta(seconds=settings.login_ip_rate_limit_window_seconds)
    from_this_address = list(
        db.scalars(
            select(AuthAttempt.created_at)
            .where(
                AuthAttempt.kind == "login",
                AuthAttempt.ip_hash == ip,
                AuthAttempt.created_at > ip_window_start,
            )
            .order_by(AuthAttempt.created_at)
        )
    )
    if len(from_this_address) >= settings.login_ip_rate_limit_requests:
        oldest = from_this_address[len(from_this_address) - settings.login_ip_rate_limit_requests]
        raise TooManyAttemptsError(
            _retry_after(oldest, settings.login_ip_rate_limit_window_seconds, now)
        )

    lockout_window_start = now - timedelta(seconds=settings.login_lockout_window_seconds)
    failures = _consecutive_failures_since_last_success(db, email, lockout_window_start)
    if len(failures) >= settings.login_lockout_attempts:
        # failures[] is newest first; the one that tipped the count over the limit is the oldest
        # of the ones counted, and it is that one ageing out of the window that ends the lockout.
        oldest_counted = failures[settings.login_lockout_attempts - 1]
        raise TooManyAttemptsError(
            _retry_after(oldest_counted, settings.login_lockout_window_seconds, now)
        )


def check_register_allowed(db: Session, *, ip: str) -> None:
    """Raises `TooManyAttemptsError` if this address has registered too many times recently."""
    now = _now()
    window_start = now - timedelta(seconds=settings.register_ip_rate_limit_window_seconds)
    from_this_address = list(
        db.scalars(
            select(AuthAttempt.created_at)
            .where(
                AuthAttempt.kind == "register",
                AuthAttempt.ip_hash == ip,
                AuthAttempt.created_at > window_start,
            )
            .order_by(AuthAttempt.created_at)
        )
    )
    if len(from_this_address) >= settings.register_ip_rate_limit_requests:
        oldest = from_this_address[
            len(from_this_address) - settings.register_ip_rate_limit_requests
        ]
        raise TooManyAttemptsError(
            _retry_after(oldest, settings.register_ip_rate_limit_window_seconds, now)
        )


def record_attempt(db: Session, *, kind: str, email: str, ip: str, succeeded: bool) -> None:
    """Records one attempt, and prunes rows old enough that no window could still need them."""
    now = _now()
    db.add(AuthAttempt(kind=kind, email=email, ip_hash=ip, succeeded=succeeded, created_at=now))
    db.execute(delete(AuthAttempt).where(AuthAttempt.created_at < now - _RETENTION))
    db.commit()
