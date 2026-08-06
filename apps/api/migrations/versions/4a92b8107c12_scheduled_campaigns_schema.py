"""scheduled campaigns schema

Revision ID: 4a92b8107c12
Revises: f5ecaa79863b
Create Date: 2026-08-06 10:15:00.000000

Adds three columns to the `campaigns` table required for the Campaign Scheduler
(GRX-SCHED-001):

- scheduled_at   — UTC datetime when the campaign should be dispatched
- cancelled_at   — UTC datetime when the campaign was cancelled (if at all)
- idempotency_key — UUID that prevents double-dispatch on worker/scheduler restart

Also:
- Expands the `ck_campaigns_status` CHECK constraint to include the new
  statuses SCHEDULED, DISPATCHING, and CANCELLED.
- Adds a composite index (status, scheduled_at) so the scheduler's polling
  query (WHERE status='SCHEDULED' AND scheduled_at <= NOW()) uses an index scan.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4a92b8107c12"
down_revision: str = "04cce299c2d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new columns (all nullable / with defaults so existing rows are valid)
    op.add_column(
        "campaigns",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column(
            "idempotency_key",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )

    # 2. Unique constraint on idempotency_key
    op.create_unique_constraint(
        "uq_campaigns_idempotency_key",
        "campaigns",
        ["idempotency_key"],
    )

    # 3. Drop old status CHECK (only covered DRAFT/SENDING/SENT/FAILED) and replace
    #    with one that covers the full scheduled-campaign lifecycle.
    op.drop_constraint("ck_campaigns_status", "campaigns", type_="check")
    op.create_check_constraint(
        "ck_campaigns_status",
        "campaigns",
        "status IN ('DRAFT', 'SCHEDULED', 'DISPATCHING', 'SENDING', 'SENT', 'CANCELLED', 'FAILED')",
    )

    # 4. Composite index for the scheduler's polling query
    op.create_index(
        "ix_campaigns_status_scheduled_at",
        "campaigns",
        ["status", "scheduled_at"],
    )


def downgrade() -> None:
    # Reverse order of upgrade
    op.drop_index("ix_campaigns_status_scheduled_at", table_name="campaigns")

    op.drop_constraint("ck_campaigns_status", "campaigns", type_="check")
    op.create_check_constraint(
        "ck_campaigns_status",
        "campaigns",
        "status IN ('DRAFT', 'SENDING', 'SENT', 'FAILED')",
    )

    op.drop_constraint("uq_campaigns_idempotency_key", "campaigns", type_="unique")
    op.drop_column("campaigns", "idempotency_key")
    op.drop_column("campaigns", "cancelled_at")
    op.drop_column("campaigns", "scheduled_at")
