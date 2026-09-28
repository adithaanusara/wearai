"""add order payment status and payment events

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-27 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("payment_status", sa.String(10), nullable=False, server_default="unpaid"),
    )
    op.add_column("orders", sa.Column("payhere_payment_id", sa.String(40)))
    op.create_check_constraint(
        "ck_orders_payment_status",
        "orders",
        "payment_status IN ('unpaid', 'pending', 'paid', 'failed')",
    )

    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("from_status", sa.String(10), nullable=False),
        sa.Column("to_status", sa.String(10), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("method", sa.String(20)),
        sa.Column("message", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_events_order_id", "payment_events", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_events_order_id", table_name="payment_events")
    op.drop_table("payment_events")
    op.drop_constraint("ck_orders_payment_status", "orders", type_="check")
    op.drop_column("orders", "payhere_payment_id")
    op.drop_column("orders", "payment_status")
