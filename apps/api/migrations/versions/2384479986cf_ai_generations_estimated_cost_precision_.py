"""ai_generations.estimated_cost_usd precision fix (Slice 6 GRX-AI-006)

Revision ID: 2384479986cf
Revises: 1004475206ab
Create Date: 2026-08-12 18:02:53.319543

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2384479986cf"
down_revision: str | Sequence[str] | None = "1004475206ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema.

    An unscaled NUMERIC column stores a Python float's exact binary representation on
    insert, producing long floating-point artifacts (e.g.
    0.000569999999999999977171...) instead of the intended rounded value -- found live
    against a real generation call. Alembic's default type comparator doesn't flag a
    precision/scale-only change as drift (confirmed: --autogenerate produced an empty
    migration here), so this is hand-written.
    """
    op.alter_column(
        "ai_generations",
        "estimated_cost_usd",
        existing_type=sa.Numeric(),
        type_=sa.Numeric(10, 6),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "ai_generations",
        "estimated_cost_usd",
        existing_type=sa.Numeric(10, 6),
        type_=sa.Numeric(),
        existing_nullable=True,
    )
