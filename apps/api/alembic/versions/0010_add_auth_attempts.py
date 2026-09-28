"""add auth attempts

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-28 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_auth_attempts_created_at", "auth_attempts", ["created_at"])
    op.create_index("ix_auth_attempts_kind", "auth_attempts", ["kind"])
    op.create_index("ix_auth_attempts_ip_hash", "auth_attempts", ["ip_hash"])
    op.create_index("ix_auth_attempts_email", "auth_attempts", ["email"])


def downgrade() -> None:
    op.drop_index("ix_auth_attempts_email", table_name="auth_attempts")
    op.drop_index("ix_auth_attempts_ip_hash", table_name="auth_attempts")
    op.drop_index("ix_auth_attempts_kind", table_name="auth_attempts")
    op.drop_index("ix_auth_attempts_created_at", table_name="auth_attempts")
    op.drop_table("auth_attempts")
