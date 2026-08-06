"""fix campaigns.idempotency_key type drift

Revision ID: caf1c42204c9
Revises: 4a92b8107c12
Create Date: 2026-08-06 18:10:00.000000

Two Sprint 4 worktrees independently authored GRX-SCHED-001. The version that
landed on main via merge (`4a92b8107c12`) defines `idempotency_key` as
`UUID NOT NULL UNIQUE` in its `upgrade()`, but a different pre-merge worktree
had already run an *earlier* draft of that same revision ID against this dev
database — one that added `idempotency_key` as a plain nullable `TEXT`
column, with no unique constraint. Because Alembic's `alembic_version`
bookkeeping only tracks the revision ID (not the migration file's content), it
still reports `4a92b8107c12` as fully applied even though the actual column
on disk no longer matches what that revision's current file defines —
confirmed via `alembic check`, which reported drift only on this column (the
scheduled_at/cancelled_at columns, the index, and the CHECK constraint all
already matched).

`campaigns` has zero rows in every environment this has been applied to, so
there's no data to migrate — this just drops and re-adds the column to match
`4a92b8107c12`'s own definition exactly, rather than editing history.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "caf1c42204c9"
down_revision: str = "4a92b8107c12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("campaigns", "idempotency_key")
    op.add_column(
        "campaigns",
        sa.Column(
            "idempotency_key",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.create_unique_constraint(
        "uq_campaigns_idempotency_key",
        "campaigns",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_campaigns_idempotency_key", "campaigns", type_="unique")
    op.drop_column("campaigns", "idempotency_key")
    op.add_column(
        "campaigns",
        sa.Column("idempotency_key", sa.Text(), nullable=True),
    )
