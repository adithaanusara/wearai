from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RecoveryCode(Base):
    """One one-time code for signing in without the authenticator app. Hashed like a password;
    a leaked database does not hand out usable codes."""

    __tablename__ = "recovery_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PendingLogin(Base):
    """A password that has already been checked, waiting on the second step.

    Short-lived and single-use, the same shape as a session (the id is the hash of a random
    token, never the token itself), but it proves nothing more than "the password was right a
    moment ago" - it cannot be used in place of a real session anywhere.
    """

    __tablename__ = "pending_logins"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
