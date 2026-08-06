"""company/brand account isolation (GRX-SAAS-001 Phase A, company/brand slice)

Revision ID: 97a0c090193b
Revises: 5e4d9cd719da
Create Date: 2026-08-07 00:30:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "97a0c090193b"
down_revision: str | Sequence[str] | None = "5e4d9cd719da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Same seeded account as 5e4d9cd719da -- every pre-multi-tenant row belongs to one
# account, not a new one per migration.
_SEED_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    """Upgrade schema."""
    for table in ("company_profile", "brand_profiles"):
        op.add_column(table, sa.Column("account_id", sa.UUID(), nullable=True))
        op.execute(
            sa.text(f"UPDATE {table} SET account_id = :account_id").bindparams(  # noqa: S608
                account_id=_SEED_ACCOUNT_ID
            )
        )
        op.alter_column(table, "account_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_account_id_accounts",
            table,
            "accounts",
            ["account_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_account_id", table, ["account_id"])


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("company_profile", "brand_profiles"):
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account_id_accounts", table, type_="foreignkey")
        op.drop_column(table, "account_id")
