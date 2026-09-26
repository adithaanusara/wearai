"""Who may chat, and how much. The counts live in the database, so they hold across processes."""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ChatUsage, User


class RateLimitedError(Exception):
    """This visitor has sent too many messages recently."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("rate limited")
        self.retry_after = retry_after


class DailyCapError(Exception):
    """The store-wide daily token budget for the assistant is used up."""


def client_key(request: Request, user: User | None) -> str:
    """A stable, anonymous id for the sender: their account, or a salted hash of their address.

    Signed-in visitors are counted by account, so several people behind one address are not
    punished for each other. The address comes from the connection itself; behind a proxy, configure
    the server to pass the real client address on (for example uvicorn --proxy-headers).
    """
    source = (
        f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    )
    return hmac.new(settings.chat_hash_salt.encode(), source.encode(), hashlib.sha256).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def start(db: Session, key: str, user: User | None) -> ChatUsage:
    """Checks the limits and records the request straight away, so it counts even if it fails."""
    now = _now()

    window_start = now - timedelta(seconds=settings.chat_rate_limit_window_seconds)
    recent = list(
        db.scalars(
            select(ChatUsage.created_at)
            .where(ChatUsage.client_hash == key, ChatUsage.created_at > window_start)
            .order_by(ChatUsage.created_at)
        )
    )
    if len(recent) >= settings.chat_rate_limit_requests:
        # The oldest request in the window leaving the window frees a slot.
        oldest = recent[len(recent) - settings.chat_rate_limit_requests]
        wait = (
            oldest + timedelta(seconds=settings.chat_rate_limit_window_seconds) - now
        ).total_seconds()
        raise RateLimitedError(max(1, int(wait) + 1))

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    used_today = db.scalar(
        select(func.coalesce(func.sum(ChatUsage.input_tokens + ChatUsage.output_tokens), 0)).where(
            ChatUsage.created_at >= day_start
        )
    )
    if (used_today or 0) >= settings.chat_daily_token_cap:
        raise DailyCapError

    usage = ChatUsage(client_hash=key, user_id=user.id if user else None, model=settings.chat_model)
    db.add(usage)
    db.commit()
    return usage


@dataclass(frozen=True)
class Outcome:
    outcome: str
    input_tokens: int = 0
    output_tokens: int = 0
    tool_rounds: int = 0
    provider_request_id: str | None = None


def finish(db: Session, usage: ChatUsage, result: Outcome) -> None:
    usage.outcome = result.outcome
    usage.input_tokens = result.input_tokens
    usage.output_tokens = result.output_tokens
    usage.tool_rounds = result.tool_rounds
    usage.provider_request_id = result.provider_request_id
    db.commit()
