"""Phase 4 Social multi-channel management and media library schema migration

Revision ID: d2e3f4a5b6c7
Revises: c7d8e9f0a1b2
Create Date: 2026-09-16 13:30:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d2e3f4a5b6c7"
down_revision: str | Sequence[str] | None = "c7d8e9f0a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update social_connections constraint to allow multi-channel providers
    op.drop_constraint("ck_social_connections_provider", "social_connections", type_="check")
    op.create_check_constraint(
        "ck_social_connections_provider",
        "social_connections",
        "provider IN ('LINKEDIN', 'TWITTER', 'INSTAGRAM_BUSINESS', 'FACEBOOK_PAGE', 'YOUTUBE')",
    )

    # 2. Make Instagram/Facebook specific fields nullable for other providers
    op.alter_column("social_connections", "ig_business_account_id", nullable=True)
    op.alter_column("social_connections", "facebook_page_id", nullable=True)

    # 3. Add generic provider account metadata fields to social_connections
    op.add_column("social_connections", sa.Column("provider_account_id", sa.Text(), nullable=True))
    op.add_column("social_connections", sa.Column("provider_username", sa.Text(), nullable=True))
    op.add_column(
        "social_connections", sa.Column("provider_account_name", sa.Text(), nullable=True)
    )
    op.add_column(
        "social_connections", sa.Column("refresh_token_encrypted", sa.Text(), nullable=True)
    )
    op.add_column(
        "social_connections",
        sa.Column(
            "account_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "social_connections",
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # 4. Add campaign and UTM parameters, and generic provider post fields to social_posts
    op.add_column(
        "social_posts",
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(op.f("ix_social_posts_campaign_id"), "social_posts", ["campaign_id"])
    op.add_column("social_posts", sa.Column("utm_source", sa.Text(), nullable=True))
    op.add_column("social_posts", sa.Column("utm_medium", sa.Text(), nullable=True))
    op.add_column("social_posts", sa.Column("utm_campaign", sa.Text(), nullable=True))
    op.add_column("social_posts", sa.Column("utm_content", sa.Text(), nullable=True))
    op.add_column("social_posts", sa.Column("provider_post_id", sa.Text(), nullable=True))
    op.add_column("social_posts", sa.Column("provider_permalink", sa.Text(), nullable=True))

    # 5. Update social_post_media constraint to allow VIDEO media type, and add file metadata
    op.drop_constraint("ck_social_post_media_media_type", "social_post_media", type_="check")
    op.create_check_constraint(
        "ck_social_post_media_media_type",
        "social_post_media",
        "media_type IN ('IMAGE', 'VIDEO')",
    )
    op.add_column("social_post_media", sa.Column("file_size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("social_post_media", sa.Column("mime_type", sa.Text(), nullable=True))

    # 6. Create media_folders table
    op.create_table(
        "media_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("media_folders.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
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
    )

    # 7. Create media_assets table
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "folder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("media_folders.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("public_url", sa.Text(), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
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
            "media_type IN ('IMAGE', 'VIDEO', 'DOCUMENT')",
            name="ck_media_assets_media_type",
        ),
    )
    op.create_index(op.f("ix_media_assets_filename"), "media_assets", ["filename"])


def downgrade() -> None:
    op.drop_table("media_assets")
    op.drop_table("media_folders")

    op.drop_column("social_post_media", "mime_type")
    op.drop_column("social_post_media", "file_size_bytes")
    op.drop_constraint("ck_social_post_media_media_type", "social_post_media", type_="check")
    op.create_check_constraint(
        "ck_social_post_media_media_type",
        "social_post_media",
        "media_type IN ('IMAGE')",
    )

    op.drop_index(op.f("ix_social_posts_campaign_id"), table_name="social_posts")
    op.drop_column("social_posts", "provider_permalink")
    op.drop_column("social_posts", "provider_post_id")
    op.drop_column("social_posts", "utm_content")
    op.drop_column("social_posts", "utm_campaign")
    op.drop_column("social_posts", "utm_medium")
    op.drop_column("social_posts", "utm_source")
    op.drop_column("social_posts", "campaign_id")

    op.drop_column("social_connections", "scopes")
    op.drop_column("social_connections", "account_metadata")
    op.drop_column("social_connections", "refresh_token_encrypted")
    op.drop_column("social_connections", "provider_account_name")
    op.drop_column("social_connections", "provider_username")
    op.drop_column("social_connections", "provider_account_id")
    op.alter_column("social_connections", "facebook_page_id", nullable=False)
    op.alter_column("social_connections", "ig_business_account_id", nullable=False)
    op.drop_constraint("ck_social_connections_provider", "social_connections", type_="check")
    op.create_check_constraint(
        "ck_social_connections_provider",
        "social_connections",
        "provider IN ('INSTAGRAM_BUSINESS')",
    )
