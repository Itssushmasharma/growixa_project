"""email templates and versions

Revision ID: d36211c53aed
Revises: 393c4222c8af
Create Date: 2026-08-03 23:33:33.711134

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d36211c53aed"
down_revision: str | Sequence[str] | None = "393c4222c8af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grants attach to the same rows.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"
ROLE_CONTENT_CREATOR = "03c1c2a9-1315-4a86-93eb-b5c936280372"
ROLE_ANALYST = "6ab3fff0-9fcb-46e0-9cdb-0c54c7032ab3"

PERM_CAMPAIGNS_MANAGE = "2c9f7b3e-4d1a-4f6e-8b2a-7e9d5c1f6a3b"
PERM_CAMPAIGNS_VIEW = "6a4e1f9c-8d3b-4a7e-9c1f-3b6e8a2d5c7f"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "email_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "email_template_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("template_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["template_id"], ["email_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version_number"),
    )

    _seed_campaigns_manage_and_view_permissions()


def _seed_campaigns_manage_and_view_permissions() -> None:
    """`campaigns.manage`/`campaigns.view` — needed starting with this task since
    templates are gated by them (see RBAC.md §Slice 3 permission codes). `campaigns.send`
    is deferred to whichever task adds the actual send action (GRX-EMAIL-004)."""
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
                "id": PERM_CAMPAIGNS_MANAGE,
                "code": "campaigns.manage",
                "description": (
                    "Create/edit email templates and campaign drafts (subject, body, "
                    "recipient targeting) — does not include sending"
                ),
            },
            {
                "id": PERM_CAMPAIGNS_VIEW,
                "code": "campaigns.view",
                "description": (
                    "Read-only access to templates, campaigns, and delivery/analytics reports"
                ),
            },
        ],
    )

    manage_roles = (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_MARKETING_MANAGER, ROLE_CONTENT_CREATOR)
    view_roles = (
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_MARKETING_MANAGER,
        ROLE_CONTENT_CREATOR,
        ROLE_ANALYST,
    )
    matrix: dict[str, tuple[str, ...]] = {
        PERM_CAMPAIGNS_MANAGE: manage_roles,
        PERM_CAMPAIGNS_VIEW: view_roles,
    }

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_id, "permission_id": permission_id}
            for permission_id, role_ids in matrix.items()
            for role_id in role_ids
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        f"('{PERM_CAMPAIGNS_MANAGE}', '{PERM_CAMPAIGNS_VIEW}')"
    )
    op.execute(
        f"DELETE FROM permissions WHERE id IN ('{PERM_CAMPAIGNS_MANAGE}', '{PERM_CAMPAIGNS_VIEW}')"
    )
    op.drop_table("email_template_versions")
    op.drop_table("email_templates")
