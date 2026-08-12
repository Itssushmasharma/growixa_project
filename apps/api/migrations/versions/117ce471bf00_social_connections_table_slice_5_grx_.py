"""social connections table (Slice 5 GRX-SOCIAL-002)

Revision ID: 117ce471bf00
Revises: 6349b268afa5
Create Date: 2026-08-12 04:44:25.631800

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "117ce471bf00"
down_revision: str | Sequence[str] | None = "6349b268afa5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grants attach to the same rows.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"
ROLE_CONTENT_CREATOR = "03c1c2a9-1315-4a86-93eb-b5c936280372"
ROLE_ANALYST = "6ab3fff0-9fcb-46e0-9cdb-0c54c7032ab3"

PERM_SOCIAL_MANAGE = "2f8b6c1a-4d3e-4a7f-9b2c-1e6a8d5f3c70"
PERM_SOCIAL_PUBLISH = "7a1d4e9c-3b6f-4c8a-8d1e-5f2b9a7c4e60"
PERM_SOCIAL_VIEW = "9c3e7a2f-6d1b-4e9c-a5f8-2b4d6e9a1c30"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "social_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("ig_business_account_id", sa.Text(), nullable=False),
        sa.Column("ig_username", sa.Text(), nullable=True),
        sa.Column("facebook_page_id", sa.Text(), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "last_connected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
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
            "provider IN ('INSTAGRAM_BUSINESS')", name="ck_social_connections_provider"
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_social_connections_account_id"), "social_connections", ["account_id"])
    op.create_index(
        "ux_social_connections_active_per_provider",
        "social_connections",
        ["account_id", "provider"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    _seed_social_permissions()


def _seed_social_permissions() -> None:
    """Slice 5 `social.manage` / `social.publish` / `social.view` permission codes, see
    RBAC.md §Slice 5 permission codes."""
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
                "id": PERM_SOCIAL_MANAGE,
                "code": "social.manage",
                "description": "Create/edit social post drafts, upload/remove media",
            },
            {
                "id": PERM_SOCIAL_PUBLISH,
                "code": "social.publish",
                "description": (
                    "Publish a post immediately, schedule a post for later, cancel a "
                    "scheduled post, retry a failed post"
                ),
            },
            {
                "id": PERM_SOCIAL_VIEW,
                "code": "social.view",
                "description": (
                    "Read-only access to posts, connection status, and the content calendar"
                ),
            },
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_SOCIAL_MANAGE},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_SOCIAL_MANAGE},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_SOCIAL_MANAGE},
            {"role_id": ROLE_CONTENT_CREATOR, "permission_id": PERM_SOCIAL_MANAGE},
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_SOCIAL_PUBLISH},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_SOCIAL_PUBLISH},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_SOCIAL_PUBLISH},
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_SOCIAL_VIEW},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_SOCIAL_VIEW},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_SOCIAL_VIEW},
            {"role_id": ROLE_CONTENT_CREATOR, "permission_id": PERM_SOCIAL_VIEW},
            {"role_id": ROLE_ANALYST, "permission_id": PERM_SOCIAL_VIEW},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        f"('{PERM_SOCIAL_MANAGE}', '{PERM_SOCIAL_PUBLISH}', '{PERM_SOCIAL_VIEW}')"
    )
    op.execute(
        "DELETE FROM permissions WHERE id IN "
        f"('{PERM_SOCIAL_MANAGE}', '{PERM_SOCIAL_PUBLISH}', '{PERM_SOCIAL_VIEW}')"
    )
    op.drop_index(
        "ux_social_connections_active_per_provider",
        table_name="social_connections",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_index(op.f("ix_social_connections_account_id"), table_name="social_connections")
    op.drop_table("social_connections")
