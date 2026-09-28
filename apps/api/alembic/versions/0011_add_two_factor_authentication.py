"""add two factor authentication

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-28 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("totp_secret_encrypted", sa.String(255)))
    op.add_column("users", sa.Column("totp_confirmed_at", sa.DateTime(timezone=True)))

    op.create_table(
        "recovery_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_recovery_codes_user_id", "recovery_codes", ["user_id"])

    op.create_table(
        "pending_logins",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pending_logins_user_id", "pending_logins", ["user_id"])
    op.create_index("ix_pending_logins_expires_at", "pending_logins", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_pending_logins_expires_at", table_name="pending_logins")
    op.drop_index("ix_pending_logins_user_id", table_name="pending_logins")
    op.drop_table("pending_logins")
    op.drop_index("ix_recovery_codes_user_id", table_name="recovery_codes")
    op.drop_table("recovery_codes")
    op.drop_column("users", "totp_confirmed_at")
    op.drop_column("users", "totp_secret_encrypted")
