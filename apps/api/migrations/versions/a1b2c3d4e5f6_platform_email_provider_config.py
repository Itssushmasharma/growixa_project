"""platform_email_provider_config table + platform.email.manage RBAC seed

Revision ID: a1b2c3d4e5f6
Revises: e3e939e991f4
Create Date: 2026-08-14 21:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "e3e939e991f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLATFORM_PERM_EMAIL_MANAGE = uuid.UUID("ef3a2bb8-a6ca-4995-bf60-b56780c30112")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "platform_email_provider_config",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("smtp_host", sa.Text(), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False),
        sa.Column("smtp_username", sa.Text(), nullable=False),
        sa.Column("smtp_password_encrypted", sa.Text(), nullable=False),
        sa.Column("from_email", sa.Text(), nullable=False),
        sa.Column("from_name", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by_platform_admin_id", sa.UUID(), nullable=True),
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
            "provider IN ('POSTMARK', 'CUSTOM_SMTP')",
            name="ck_platform_email_provider_config_provider",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_platform_admin_id"],
            ["platform_admins.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_platform_email_provider_config_active",
        "platform_email_provider_config",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.email.manage', "
            "'View/edit the platform-wide email provider configuration used for "
            "system/transactional email (e.g. registration verification)')"
        ).bindparams(id=PLATFORM_PERM_EMAIL_MANAGE)
    )
    for role in ("platform.owner", "platform.admin"):
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=PLATFORM_PERM_EMAIL_MANAGE)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_role_permissions WHERE permission_id = :id").bindparams(
            id=PLATFORM_PERM_EMAIL_MANAGE
        )
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE id = :id").bindparams(
            id=PLATFORM_PERM_EMAIL_MANAGE
        )
    )
    op.drop_index(
        "ux_platform_email_provider_config_active",
        table_name="platform_email_provider_config",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_table("platform_email_provider_config")
