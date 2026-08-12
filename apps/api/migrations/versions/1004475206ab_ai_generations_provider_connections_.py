"""ai_generations, ai_provider_connections, platform_ai_provider_config tables (Slice 6 GRX-AI-002)

Revision ID: 1004475206ab
Revises: 5f1e2783a91f
Create Date: 2026-08-12 17:00:15.831126

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1004475206ab"
down_revision: str | Sequence[str] | None = "5f1e2783a91f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed role IDs from d330e8b64b48 (RBAC.md's seeded roles) — reused here, not
# re-generated, so the new grants attach to the same rows.
ROLE_SUPER_ADMIN = "f654ec88-ba59-4cd2-a74a-032cec74c422"
ROLE_ADMIN = "8c7ebd1a-f1fe-4d22-bb7f-29c79d0444ce"
ROLE_MARKETING_MANAGER = "6b7dc157-82c4-4878-b12d-826b67cf7181"
ROLE_CONTENT_CREATOR = "03c1c2a9-1315-4a86-93eb-b5c936280372"
ROLE_ANALYST = "6ab3fff0-9fcb-46e0-9cdb-0c54c7032ab3"

PERM_AI_MANAGE = "24ec7b18-a2aa-4c6d-b3eb-cf0bb16ba2d8"
PERM_AI_VIEW = "715f395a-d073-41e8-9c35-deced24d75b8"

PLATFORM_PERM_AI_MANAGE = uuid.UUID("b6f2a1e4-9c3d-4a7f-8e1b-5d2c6f9a3b40")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "platform_ai_provider_config",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("default_model", sa.Text(), nullable=False),
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
            "provider IN ('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'OLLAMA')",
            name="ck_platform_ai_provider_config_provider",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_platform_admin_id"],
            ["platform_admins.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_platform_ai_provider_config_active",
        "platform_ai_provider_config",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.create_table(
        "ai_generations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column("capability", sa.Text(), nullable=False),
        sa.Column("prompt_template_key", sa.Text(), nullable=False),
        sa.Column("input_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("linked_entity_type", sa.Text(), nullable=True),
        sa.Column("linked_entity_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "capability IN ("
            "'SUBJECT_LINE', 'BODY_COPY', 'SOCIAL_CAPTION', 'REWRITE', 'HASHTAGS', "
            "'POSTING_TIME'"
            ")",
            name="ck_ai_generations_capability",
        ),
        sa.CheckConstraint("status IN ('COMPLETE', 'FAILED')", name="ck_ai_generations_status"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_generations_account_id"), "ai_generations", ["account_id"], unique=False
    )
    op.create_index(
        "ix_ai_generations_account_id_capability",
        "ai_generations",
        ["account_id", "capability"],
        unique=False,
    )
    op.create_table(
        "ai_provider_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("default_model", sa.Text(), nullable=False),
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
            "provider IN ('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'OLLAMA')",
            name="ck_ai_provider_connections_provider",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_provider_connections_account_id"),
        "ai_provider_connections",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ux_ai_provider_connections_active_per_account",
        "ai_provider_connections",
        ["account_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    _seed_ai_permissions()


def _seed_ai_permissions() -> None:
    """Slice 6 `ai.manage` / `ai.view` (customer RBAC) and `platform.ai.manage`
    (platform RBAC) permission codes, see RBAC.md §Slice 6 permission codes and
    §Sprint 7 — Platform AI config."""
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
                "id": PERM_AI_MANAGE,
                "code": "ai.manage",
                "description": (
                    "Generate/rewrite AI content (subject lines, body copy, social "
                    "captions, hashtags, posting-time suggestions)"
                ),
            },
            {
                "id": PERM_AI_VIEW,
                "code": "ai.view",
                "description": "Read-only access to generation history",
            },
        ],
    )

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_AI_MANAGE},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_AI_MANAGE},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_AI_MANAGE},
            {"role_id": ROLE_CONTENT_CREATOR, "permission_id": PERM_AI_MANAGE},
            {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_AI_VIEW},
            {"role_id": ROLE_ADMIN, "permission_id": PERM_AI_VIEW},
            {"role_id": ROLE_MARKETING_MANAGER, "permission_id": PERM_AI_VIEW},
            {"role_id": ROLE_CONTENT_CREATOR, "permission_id": PERM_AI_VIEW},
            {"role_id": ROLE_ANALYST, "permission_id": PERM_AI_VIEW},
        ],
    )

    op.execute(
        sa.text(
            "INSERT INTO platform_permissions (id, code, description) "
            "VALUES (:id, 'platform.ai.manage', "
            "'View/edit the platform-wide default AI provider configuration')"
        ).bindparams(id=PLATFORM_PERM_AI_MANAGE)
    )
    for role in ("platform.owner", "platform.admin"):
        op.execute(
            sa.text(
                "INSERT INTO platform_role_permissions (role, permission_id) "
                "VALUES (:role, :permission_id)"
            ).bindparams(role=role, permission_id=PLATFORM_PERM_AI_MANAGE)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("DELETE FROM platform_role_permissions WHERE permission_id = :id").bindparams(
            id=PLATFORM_PERM_AI_MANAGE
        )
    )
    op.execute(
        sa.text("DELETE FROM platform_permissions WHERE id = :id").bindparams(
            id=PLATFORM_PERM_AI_MANAGE
        )
    )
    op.execute(
        "DELETE FROM role_permissions WHERE permission_id IN "
        f"('{PERM_AI_MANAGE}', '{PERM_AI_VIEW}')"
    )
    op.execute(f"DELETE FROM permissions WHERE id IN ('{PERM_AI_MANAGE}', '{PERM_AI_VIEW}')")

    op.drop_index(
        "ux_ai_provider_connections_active_per_account",
        table_name="ai_provider_connections",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_index(
        op.f("ix_ai_provider_connections_account_id"), table_name="ai_provider_connections"
    )
    op.drop_table("ai_provider_connections")
    op.drop_index("ix_ai_generations_account_id_capability", table_name="ai_generations")
    op.drop_index(op.f("ix_ai_generations_account_id"), table_name="ai_generations")
    op.drop_table("ai_generations")
    op.drop_index(
        "ux_platform_ai_provider_config_active",
        table_name="platform_ai_provider_config",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_table("platform_ai_provider_config")
