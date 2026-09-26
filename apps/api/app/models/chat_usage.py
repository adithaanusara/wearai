from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

OUTCOMES = ("started", "ok", "refused", "truncated", "error")


class ChatUsage(Base):
    """One row per chat request: who (as a hash), how much, and how it ended.

    It holds the counts that the limits and the cost cap need, and never the message text.
    """

    __tablename__ = "chat_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    # A salted hash of the visitor's address, or of their account id when signed in.
    client_hash: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    model: Mapped[str] = mapped_column(String(60), default="")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_rounds: Mapped[int] = mapped_column(SmallInteger, default=0)
    outcome: Mapped[str] = mapped_column(String(12), default="started")
    # The provider's request id, useful when reporting a problem to them.
    provider_request_id: Mapped[str | None] = mapped_column(String(80))
