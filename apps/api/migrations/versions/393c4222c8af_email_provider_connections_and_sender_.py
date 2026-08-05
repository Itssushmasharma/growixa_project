"""email provider connections and sender identities

Revision ID: 393c4222c8af
Revises: 97642610fb46
Create Date: 2026-08-03 23:10:32.376289

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "393c4222c8af"
down_revision: str | Sequence[str] | None = "97642610fb46"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grant attaches to the same row.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"

PERM_INTEGRATIONS_MANAGE = "1b7f6a5e-6e3e-4a2f-9c6b-3a2f8c9d4e10"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "email_provider_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("smtp_host", sa.Text(), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False),
        sa.Column("smtp_username", sa.Text(), nullable=False),
        sa.Column("smtp_password_encrypted", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.CheckConstraint(
            "provider IN ('POSTMARK')", name="ck_email_provider_connections_provider"
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_provider_connections_active",
        "email_provider_connections",
        ["is_active"],
        unique=False,
        postgresql_where=sa.text("is_active"),
    )
    op.create_table(
        "sender_identities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email_provider_connection_id", sa.UUID(), nullable=False),
        sa.Column("from_email", postgresql.CITEXT(), nullable=False),
        sa.Column("from_name", sa.Text(), nullable=False),
        sa.Column("reply_to_email", postgresql.CITEXT(), nullable=True),
        sa.Column("verification_status", sa.Text(), server_default="PENDING", nullable=False),
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
        sa.CheckConstraint(
            "verification_status IN ('PENDING', 'VERIFIED', 'FAILED')",
            name="ck_sender_identities_verification_status",
        ),
        sa.ForeignKeyConstraint(
            ["email_provider_connection_id"], ["email_provider_connections.id"]
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    _seed_integrations_permissions()


def _seed_integrations_permissions() -> None:
    """Slice 3 `integrations.manage` permission code — Super-Admin-only, see
    RBAC.md §Slice 3 permission codes."""
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
                "id": PERM_INTEGRATIONS_MANAGE,
                "code": "integrations.manage",
                "description": (
                    "Manage email provider connections and sender identities, including "
                    "SMTP credentials"
                ),
            },
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [{"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_INTEGRATIONS_MANAGE}],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"DELETE FROM role_permissions WHERE permission_id = '{PERM_INTEGRATIONS_MANAGE}'")
    op.execute(f"DELETE FROM permissions WHERE id = '{PERM_INTEGRATIONS_MANAGE}'")
    op.drop_table("sender_identities")
    op.drop_index("ix_email_provider_connections_active", table_name="email_provider_connections")
    op.drop_table("email_provider_connections")
