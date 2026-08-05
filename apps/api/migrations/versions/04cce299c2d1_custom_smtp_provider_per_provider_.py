"""custom smtp provider, per-provider active connections

Revision ID: 04cce299c2d1
Revises: f5ecaa79863b
Create Date: 2026-08-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "04cce299c2d1"
down_revision: str | Sequence[str] | None = "f5ecaa79863b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # GRX-EMAIL-011 / DEC-GRX-016: a second provider (generic Custom SMTP, no webhook
    # events) alongside Postmark. "One active connection globally" becomes "one active
    # connection per provider" — replacing the app-only singleton convention with a
    # real DB-enforced partial unique index.
    op.drop_constraint(
        "ck_email_provider_connections_provider",
        "email_provider_connections",
        type_="check",
    )
    op.create_check_constraint(
        "ck_email_provider_connections_provider",
        "email_provider_connections",
        "provider IN ('POSTMARK', 'CUSTOM_SMTP')",
    )

    op.drop_index("ix_email_provider_connections_active", table_name="email_provider_connections")
    op.create_index(
        "ux_email_provider_connections_active_per_provider",
        "email_provider_connections",
        ["provider"],
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
        "ix_email_provider_connections_active",
        "email_provider_connections",
        ["is_active"],
        unique=False,
        postgresql_where=sa.text("is_active"),
    )

    op.drop_constraint(
        "ck_email_provider_connections_provider",
        "email_provider_connections",
        type_="check",
    )
    op.create_check_constraint(
        "ck_email_provider_connections_provider",
        "email_provider_connections",
        "provider IN ('POSTMARK')",
    )
