"""contact soft deletion deleted_at column + partial unique index (GRX-CONTACT-010, DEC-GRX-034)

Revision ID: c1d2e3f4a5b6
Revises: 039f01bed830
Create Date: 2026-08-16 23:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "039f01bed830"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "contacts",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_constraint("ux_contacts_account_id_email", "contacts", type_="unique")
    op.create_index(
        "ux_contacts_account_id_email",
        "contacts",
        ["account_id", "email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ux_contacts_account_id_email",
        table_name="contacts",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_unique_constraint("ux_contacts_account_id_email", "contacts", ["account_id", "email"])
    op.drop_column("contacts", "deleted_at")
