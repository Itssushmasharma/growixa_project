"""campaigns versions and recipients

Revision ID: d7fa144e5c60
Revises: d36211c53aed
Create Date: 2026-08-03 23:49:48.331669

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d7fa144e5c60"
down_revision: str | Sequence[str] | None = "d36211c53aed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "campaigns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("template_id", sa.UUID(), nullable=True),
        sa.Column("sender_identity_id", sa.UUID(), nullable=False),
        sa.Column("recipient_type", sa.Text(), nullable=False),
        sa.Column("recipient_segment_id", sa.UUID(), nullable=True),
        sa.Column("recipient_list_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.Text(), server_default="DRAFT", nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "recipient_type IN ('SEGMENT', 'LIST', 'ALL_CONTACTS')",
            name="ck_campaigns_recipient_type",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SENDING', 'SENT', 'FAILED')", name="ck_campaigns_status"
        ),
        sa.ForeignKeyConstraint(["template_id"], ["email_templates.id"]),
        sa.ForeignKeyConstraint(["sender_identity_id"], ["sender_identities.id"]),
        sa.ForeignKeyConstraint(["recipient_segment_id"], ["segments.id"]),
        sa.ForeignKeyConstraint(["recipient_list_id"], ["contact_lists.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "campaign_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("campaign_id", sa.UUID(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("recipient_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_campaign_versions_campaign_id", "campaign_versions", ["campaign_id"], unique=False
    )
    op.create_table(
        "campaign_recipients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("campaign_id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("status", sa.Text(), server_default="PENDING", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'SENT', 'FAILED', 'SUPPRESSED')",
            name="ck_campaign_recipients_status",
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_campaign_recipients_campaign_id_status",
        "campaign_recipients",
        ["campaign_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_campaign_recipients_campaign_id_status", table_name="campaign_recipients")
    op.drop_table("campaign_recipients")
    op.drop_index("ix_campaign_versions_campaign_id", table_name="campaign_versions")
    op.drop_table("campaign_versions")
    op.drop_table("campaigns")
