"""contacts account isolation (GRX-SAAS-001 Phase A, contacts slice)

Revision ID: bc7589115dc5
Revises: 97a0c090193b
Create Date: 2026-08-07 00:45:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bc7589115dc5"
down_revision: str | Sequence[str] | None = "97a0c090193b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Same seeded account as 5e4d9cd719da / 97a0c090193b -- every pre-multi-tenant row
# belongs to one account, not a new one per migration.
_SEED_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

_TABLES = (
    "contacts",
    "contact_custom_fields",
    "contact_field_values",
    "tags",
    "contact_tags",
    "contact_lists",
    "contact_list_members",
    "segments",
    "segment_rules",
    "segment_members",
    "contact_imports",
    "contact_import_rows",
    "consent_records",
    "suppression_entries",
)

# (table, old global-unique constraint, new composite-unique constraint, columns)
_UNIQUE_SWAPS = (
    ("contacts", "contacts_email_key", "ux_contacts_account_id_email", ["account_id", "email"]),
    (
        "contact_custom_fields",
        "contact_custom_fields_key_key",
        "ux_contact_custom_fields_account_id_key",
        ["account_id", "key"],
    ),
    ("tags", "tags_name_key", "ux_tags_account_id_name", ["account_id", "name"]),
    (
        "suppression_entries",
        "suppression_entries_email_key",
        "ux_suppression_entries_account_id_email",
        ["account_id", "email"],
    ),
)


def upgrade() -> None:
    """Upgrade schema."""
    for table in _TABLES:
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

    for table, old_name, new_name, columns in _UNIQUE_SWAPS:
        op.drop_constraint(old_name, table, type_="unique")
        op.create_unique_constraint(new_name, table, columns)


def downgrade() -> None:
    """Downgrade schema."""
    for table, old_name, new_name, columns in _UNIQUE_SWAPS:
        op.drop_constraint(new_name, table, type_="unique")
        op.create_unique_constraint(old_name, table, [columns[1]])

    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account_id_accounts", table, type_="foreignkey")
        op.drop_column(table, "account_id")
