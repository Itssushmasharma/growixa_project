"""suppression_entries domain-level blocking support

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("suppression_entries", "email", existing_type=sa.Text(), nullable=True)
    op.add_column("suppression_entries", sa.Column("domain", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_suppression_entries_email_xor_domain",
        "suppression_entries",
        "(email IS NOT NULL AND domain IS NULL) OR (email IS NULL AND domain IS NOT NULL)",
    )
    op.create_index(
        "ux_suppression_entries_account_id_domain",
        "suppression_entries",
        ["account_id", "domain"],
        unique=True,
        postgresql_where=sa.text("domain IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ux_suppression_entries_account_id_domain",
        table_name="suppression_entries",
        postgresql_where=sa.text("domain IS NOT NULL"),
    )
    op.drop_constraint("ck_suppression_entries_email_xor_domain", "suppression_entries")
    op.drop_column("suppression_entries", "domain")
    op.alter_column("suppression_entries", "email", existing_type=sa.Text(), nullable=False)
