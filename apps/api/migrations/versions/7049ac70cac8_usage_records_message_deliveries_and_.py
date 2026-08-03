"""usage records message deliveries and delivery attempts

Revision ID: 7049ac70cac8
Revises: d7fa144e5c60
Create Date: 2026-08-04 00:19:46.717052

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7049ac70cac8"
down_revision: str | Sequence[str] | None = "d7fa144e5c60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grant attaches to the same rows.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"

PERM_CAMPAIGNS_SEND = "9d4a1f7e-2c6b-4e8f-a3d5-7c1b9e4f6a2d"


def upgrade() -> None:
    """Upgrade schema."""
    # `usage_records`: documented as existing since Sprint 1 (DEC-GRX-007) but never
    # actually created then — a genuine gap this task discovered while implementing its
    # own "usage_records gets its first real write" acceptance criterion.
    op.create_table(
        "usage_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("operation_type", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_usage_records_operation_type_created_at",
        "usage_records",
        ["operation_type", "created_at"],
        unique=False,
    )

    op.create_table(
        "message_deliveries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("campaign_recipient_id", sa.UUID(), nullable=False),
        sa.Column("provider_message_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="QUEUED", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('QUEUED', 'SENT', 'DELIVERED', 'BOUNCED', 'COMPLAINED', 'FAILED')",
            name="ck_message_deliveries_status",
        ),
        sa.ForeignKeyConstraint(
            ["campaign_recipient_id"], ["campaign_recipients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_message_deliveries_provider_message_id",
        "message_deliveries",
        ["provider_message_id"],
        unique=False,
    )

    op.create_table(
        "delivery_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_delivery_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_delivery_id"], ["message_deliveries.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_delivery_attempts_message_delivery_id",
        "delivery_attempts",
        ["message_delivery_id"],
        unique=False,
    )

    _seed_campaigns_send_permission()


def _seed_campaigns_send_permission() -> None:
    """`campaigns.send` — Super Admin/Admin/Marketing Manager only; Content Creator has
    `campaigns.manage` but deliberately not this, per RBAC.md §Slice 3 permission codes."""
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.Text()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    op.bulk_insert(
        permissions_table,
        [
            {
                "id": PERM_CAMPAIGNS_SEND,
                "code": "campaigns.send",
                "description": "Send a test email or trigger a campaign's immediate send",
            },
        ],
    )
    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_id, "permission_id": PERM_CAMPAIGNS_SEND}
            for role_id in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_MARKETING_MANAGER)
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"DELETE FROM role_permissions WHERE permission_id = '{PERM_CAMPAIGNS_SEND}'")
    op.execute(f"DELETE FROM permissions WHERE id = '{PERM_CAMPAIGNS_SEND}'")
    op.drop_index("ix_delivery_attempts_message_delivery_id", table_name="delivery_attempts")
    op.drop_table("delivery_attempts")
    op.drop_index("ix_message_deliveries_provider_message_id", table_name="message_deliveries")
    op.drop_table("message_deliveries")
    op.drop_index("ix_usage_records_operation_type_created_at", table_name="usage_records")
    op.drop_table("usage_records")
