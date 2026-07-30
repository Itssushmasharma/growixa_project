"""contacts schema

Revision ID: 209d29349ccf
Revises: bb25de08ba84
Create Date: 2026-07-30 21:44:02.495623

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "209d29349ccf"
down_revision: str | Sequence[str] | None = "bb25de08ba84"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grants attach to the same rows.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"
ROLE_ANALYST = "6ab3fff0-9fcb-46e0-9cdb-0c54c7032ab3"

PERM_CONTACTS_MANAGE = "433c4e99-6fa0-4f1f-9e43-cc6426482187"
PERM_CONTACTS_VIEW = "e7a66131-9c42-4622-8382-d0a6ef8913b9"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "contact_custom_fields",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("field_type", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "field_type IN ('TEXT', 'NUMBER', 'DATE', 'BOOLEAN')",
            name="ck_contact_custom_fields_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "contacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("first_name", sa.Text(), nullable=True),
        sa.Column("last_name", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="ACTIVE", nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
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
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_contacts_status"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "contact_field_values",
        sa.Column("contact_id", sa.UUID(), nullable=False),
        sa.Column("field_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["contact_custom_fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("contact_id", "field_id"),
    )

    _seed_contacts_permissions()


def _seed_contacts_permissions() -> None:
    """Slice 2 `contacts.manage`/`contacts.view` permission codes and role grants — see
    RBAC.md §Slice 2 permission codes."""
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
                "id": PERM_CONTACTS_MANAGE,
                "code": "contacts.manage",
                "description": (
                    "Create/edit/archive contacts; manage tags, lists, segments, custom "
                    "fields; run CSV imports; record consent; suppress addresses"
                ),
            },
            {
                "id": PERM_CONTACTS_VIEW,
                "code": "contacts.view",
                "description": "Read-only access to contacts, tags, lists, and segments",
            },
        ],
    )

    manage_roles = (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_MARKETING_MANAGER)
    view_roles = (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_MARKETING_MANAGER, ROLE_ANALYST)
    matrix: dict[str, tuple[str, ...]] = {
        PERM_CONTACTS_MANAGE: manage_roles,
        PERM_CONTACTS_VIEW: view_roles,
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
        f"('{PERM_CONTACTS_MANAGE}', '{PERM_CONTACTS_VIEW}')"
    )
    op.execute(
        f"DELETE FROM permissions WHERE id IN ('{PERM_CONTACTS_MANAGE}', '{PERM_CONTACTS_VIEW}')"
    )
    op.drop_table("contact_field_values")
    op.drop_table("contacts")
    op.drop_table("contact_custom_fields")
