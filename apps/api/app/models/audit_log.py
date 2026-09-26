from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AuditLog(Base):
    """A record of something staff did. Rows are only ever added, never changed or deleted."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Kept as text too, so the record still says who acted after an account is gone.
    actor_email: Mapped[str] = mapped_column(String(254))
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[str] = mapped_column(String(60))
    # A small summary such as {"from": "customer", "to": "staff"}. Never secrets.
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
