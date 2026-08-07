"""email/campaigns/integrations account isolation (GRX-SAAS-001 Phase A, email slice)

Revision ID: 76a6d9161aed
Revises: bc7589115dc5
Create Date: 2026-08-07 01:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "76a6d9161aed"
down_revision: str | Sequence[str] | None = "bc7589115dc5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Same seeded account as every prior GRX-SAAS-001 migration -- every pre-multi-tenant row
# belongs to one account, not a new one per migration.
_SEED_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

_TABLES = (
    "email_templates",
    "email_template_versions",
    "email_provider_connections",
    "sender_identities",
    "campaigns",
    "campaign_versions",
    "campaign_recipients",
    "message_deliveries",
    "delivery_attempts",
    "email_events",
    "unsubscribe_events",
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

    # GRX-EMAIL-011's "one active connection per provider" partial unique index becomes
    # "one active connection per provider per account" -- same index name, now composite.
    op.drop_index(
        "ux_email_provider_connections_active_per_provider",
        table_name="email_provider_connections",
    )
    op.create_index(
        "ux_email_provider_connections_active_per_provider",
        "email_provider_connections",
        ["account_id", "provider"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ux_email_provider_connections_active_per_provider",
        table_name="email_provider_connections",
    )
    op.create_index(
        "ux_email_provider_connections_active_per_provider",
        "email_provider_connections",
        ["provider"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account_id_accounts", table, type_="foreignkey")
        op.drop_column(table, "account_id")
