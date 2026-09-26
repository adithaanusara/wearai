from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"
    # Emails are stored lowercase so uniqueness does not depend on capitalisation.
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
        CheckConstraint("role IN ('customer', 'staff', 'admin')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    # Only a salted hash is ever stored, never the password itself.
    password_hash: Mapped[str] = mapped_column(String(255))
    # What the person may do. Everyone starts as a customer; staff and admin are only ever granted
    # from the command line or by an admin, never through the public website.
    role: Mapped[str] = mapped_column(String(10), default="customer", server_default="customer")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
