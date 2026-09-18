import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class SocialConnection(Base):
    __tablename__ = "social_connections"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('LINKEDIN', 'TWITTER', 'INSTAGRAM_BUSINESS', 'FACEBOOK_PAGE', 'YOUTUBE')",
            name="ck_social_connections_provider",
        ),
        # One active connection per account per provider -- identical shape to
        # ux_email_provider_connections_active_per_provider (DEC-GRX-016). Reconnecting
        # deactivates the prior row and creates a fresh one.
        Index(
            "ux_social_connections_active_per_provider",
            "account_id",
            "provider",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    ig_business_account_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ig_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    facebook_page_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_account_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_account_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Fernet-encrypted at the service layer before insert, per DEC-GRX-025. See
    # growixa_api.auth.encryption.
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    scopes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SocialPost(Base):
    __tablename__ = "social_posts"
    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'DRAFT', 'REVIEW', 'CHANGES_REQUESTED', 'APPROVED', 'SCHEDULED', 'DISPATCHING', 'PUBLISHING', 'PUBLISHED', "
            "'CANCELLED', 'FAILED'"
            ")",
            name="ck_social_posts_status",
        ),
        # Composite index for scheduler polling, identical rationale to
        # ix_campaigns_status_scheduled_at: WHERE status='SCHEDULED' AND scheduled_at <= NOW()
        Index("ix_social_posts_status_scheduled_at", "status", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    social_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_connections.id"), nullable=False
    )
    caption: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="DRAFT")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Idempotency key prevents double-publish when the scheduler or worker restarts
    # between state transitions -- identical role to campaigns.idempotency_key.
    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    utm_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(Text, nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(Text, nullable=True)
    utm_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    ig_media_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ig_permalink: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_post_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_permalink: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SocialPostMedia(Base):
    __tablename__ = "social_post_media"
    __table_args__ = (
        CheckConstraint("media_type IN ('IMAGE', 'VIDEO')", name="ck_social_post_media_media_type"),
        Index("ix_social_post_media_social_post_id", "social_post_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from social_post_id's own account_id -- see campaigns.CampaignVersion's
    # identical note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    social_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False
    )
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    public_url: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SocialPostVersion(Base):
    """Exactly one row per post, written when the worker successfully publishes it
    (GRX-SOCIAL-008) -- an immutable "what was actually published" snapshot, distinct
    from the mutable draft on `SocialPost` itself. Doubles as the worker's DB-level
    idempotency guard: its existence for a post is the authoritative "already
    published" check, mirroring campaigns.CampaignVersion's identical dual role. Not
    populated by this task."""

    __tablename__ = "social_post_versions"
    __table_args__ = (Index("ix_social_post_versions_social_post_id", "social_post_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from social_post_id's own account_id -- see campaigns.CampaignVersion's
    # identical note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    social_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_posts.id"), nullable=False
    )
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    # [{storage_path, public_url, media_type}, ...] at publish time.
    media_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    ig_media_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
