"""platform_email_validation_provider_config table + platform.validation.manage perm (GRX-SAAS-016)

Revision ID: fa291f6b37ca
Revises: b2c3d4e5f6a7
Create Date: 2026-08-15 17:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa291f6b37ca"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLATFORM_PERM_VALIDATION_MANAGE = uuid.UUID("d3e4f5a6-b7c8-49d0-a1e2-f3b4c5d6e7f8")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "platform_email_validation_provider_config",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
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
            "provider IN ('CLEAROUT')",
            name="ck_platform_email_validation_provider_config_provider",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_platform_admin_id"],
            ["platform_admins.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_platform_email_validation_provider_config_active",
        "platform_email_validation_provider_config",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.validation.manage', "
            "'View/edit the platform-wide email-validation vendor configuration '"
            "'(real-time mailbox verification for paid-plan accounts)')"
        ).bindparams(id=PLATFORM_PERM_VALIDATION_MANAGE)
    )
    for role in ("platform.owner", "platform.admin"):
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=PLATFORM_PERM_VALIDATION_MANAGE)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_role_permissions WHERE permission_id = :id").bindparams(
            id=PLATFORM_PERM_VALIDATION_MANAGE
        )
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE id = :id").bindparams(
            id=PLATFORM_PERM_VALIDATION_MANAGE
        )
    )
    op.drop_index(
        "ux_platform_email_validation_provider_config_active",
        table_name="platform_email_validation_provider_config",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_table("platform_email_validation_provider_config")
