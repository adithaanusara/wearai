from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

KINDS = ("login", "register")


class AuthAttempt(Base):
    """One sign-in or registration attempt: who (as a hash and the email involved) and whether it
    worked. Holds only what the rate limits and lockout need, never a password."""

    __tablename__ = "auth_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    kind: Mapped[str] = mapped_column(String(10), index=True)
    # A salted hash of the caller's address, never the address itself.
    ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    succeeded: Mapped[bool] = mapped_column(Boolean)
