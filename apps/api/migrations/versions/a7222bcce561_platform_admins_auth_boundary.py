"""platform admins auth boundary (GRX-SAAS-002 Phase B)

Revision ID: a7222bcce561
Revises: 0d7bf0c46ead
Create Date: 2026-08-07 14:34:30.133166

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a7222bcce561"
down_revision: str | Sequence[str] | None = "0d7bf0c46ead"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLES = (
    "platform.owner",
    "platform.admin",
    "platform.support",
    "platform.finance",
    "platform.operations",
)

_ACCESS_PERMISSION_ID = uuid.uuid4()


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "platform_admins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(f"role IN {_ROLES!r}", name="ck_platform_admins_role"),
        sa.CheckConstraint("status IN ('ACTIVE', 'DISABLED')", name="ck_platform_admins_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "platform_permissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "platform_role_permissions",
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.CheckConstraint(f"role IN {_ROLES!r}", name="ck_platform_role_permissions_role"),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["platform_permissions.id"],
            name="fk_platform_role_permissions_permission_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role", "permission_id"),
    )

    # Seed data: Phase B's one permission code, granted to every role -- see
    # DATA_MODEL.md's Sprint 5 Phase B entities section for why role differentiation is
    # deliberately deferred to each Phase E feature's own permission code.
    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.access', "
            "'Minimal gate proving a platform-admin session can reach a platform-only route')"
        ).bindparams(id=_ACCESS_PERMISSION_ID)
    )
    for role in _ROLES:
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=_ACCESS_PERMISSION_ID)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("platform_role_permissions")
    op.drop_table("platform_permissions")
    op.drop_table("platform_admins")
