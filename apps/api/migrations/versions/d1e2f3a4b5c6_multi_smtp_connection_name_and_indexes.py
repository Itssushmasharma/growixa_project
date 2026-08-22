"""multi-smtp connection name and partial unique indexes (GRX-EMAIL-013, DEC-GRX-035)

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-08-22 20:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add `name` column to email_provider_connections
    op.add_column(
        "email_provider_connections",
        sa.Column("name", sa.Text(), nullable=True),
    )
    # Default name to smtp_host for existing rows
    op.execute(sa.text("UPDATE email_provider_connections SET name = smtp_host WHERE name IS NULL"))
    op.alter_column(
        "email_provider_connections",
        "name",
        nullable=False,
    )

    # 2. Drop old partial unique index that capped CUSTOM_SMTP at 1 active row per account
    op.drop_index(
        "ux_email_provider_connections_active_per_provider",
        table_name="email_provider_connections",
    )

    # 3. Create partial unique index enforcing 1 active POSTMARK connection per account
    op.create_index(
        "ux_email_provider_connections_active_postmark",
        "email_provider_connections",
        ["account_id", "provider"],
        unique=True,
        postgresql_where=sa.text("is_active AND provider = 'POSTMARK'"),
    )

    # 4. Create partial unique index enforcing unique name among active connections per account
    op.create_index(
        "ux_email_provider_connections_active_account_name",
        "email_provider_connections",
        ["account_id", "name"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ux_email_provider_connections_active_account_name",
        table_name="email_provider_connections",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_index(
        "ux_email_provider_connections_active_postmark",
        table_name="email_provider_connections",
        postgresql_where=sa.text("is_active AND provider = 'POSTMARK'"),
    )
    op.create_index(
        "ux_email_provider_connections_active_per_provider",
        "email_provider_connections",
        ["account_id", "provider"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.drop_column("email_provider_connections", "name")
