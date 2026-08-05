"""webhook credentials email events unsubscribe events

Revision ID: f5ecaa79863b
Revises: 7049ac70cac8
Create Date: 2026-08-04 01:02:33.970875

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f5ecaa79863b"
down_revision: str | Sequence[str] | None = "7049ac70cac8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # THREAT_MODEL.md's T14: webhook Basic Auth credentials stored alongside the
    # provider connection, encrypted at rest. Nullable — no backfill needed, no
    # connection created before this migration has them, and the webhook receiver
    # fails closed on NULL.
    op.add_column(
        "email_provider_connections", sa.Column("webhook_username", sa.Text(), nullable=True)
    )
    op.add_column(
        "email_provider_connections",
        sa.Column("webhook_password_encrypted", sa.Text(), nullable=True),
    )

    op.create_table(
        "email_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_delivery_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('DELIVERED', 'OPENED', 'CLICKED', 'BOUNCED', 'COMPLAINED')",
            name="ck_email_events_event_type",
        ),
        sa.ForeignKeyConstraint(
            ["message_delivery_id"], ["message_deliveries.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_events_message_delivery_id", "email_events", ["message_delivery_id"])

    op.create_table(
        "unsubscribe_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=True),
        sa.Column("campaign_id", sa.UUID(), nullable=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_unsubscribe_events_email", "unsubscribe_events", ["email"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_unsubscribe_events_email", table_name="unsubscribe_events")
    op.drop_table("unsubscribe_events")
    op.drop_index("ix_email_events_message_delivery_id", table_name="email_events")
    op.drop_table("email_events")
    op.drop_column("email_provider_connections", "webhook_password_encrypted")
    op.drop_column("email_provider_connections", "webhook_username")
