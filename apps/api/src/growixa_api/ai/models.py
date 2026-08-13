import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base

_PROVIDER_CHECK = "provider IN ('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'OLLAMA')"


class AIGeneration(Base):
    """Write-once record of one AI generation call -- input, output, provider/model
    actually used, token usage, and estimated cost, satisfying GRX-AI-006's logging
    requirement in one table. Per DEC-GRX-028, prompt versioning is a plain code-defined
    string key, not a foreign key into a template table."""

    __tablename__ = "ai_generations"
    __table_args__ = (
        CheckConstraint(
            "capability IN ("
            "'SUBJECT_LINE', 'BODY_COPY', 'SOCIAL_CAPTION', 'REWRITE', 'HASHTAGS', "
            "'POSTING_TIME'"
            ")",
            name="ck_ai_generations_capability",
        ),
        CheckConstraint("status IN ('COMPLETE', 'FAILED')", name="ck_ai_generations_status"),
        Index("ix_ai_generations_account_id_capability", "account_id", "capability"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    capability: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_template_key: Mapped[str] = mapped_column(Text, nullable=False)
    input_context: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    output: Mapped[dict[str, object] | list[object] | None] = mapped_column(JSONB, nullable=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Fixed precision/scale (not plain Numeric) -- an unscaled NUMERIC column stores a
    # Python float's exact binary representation, producing long floating-point
    # artifacts (e.g. 0.000569999999999999977...) instead of the intended rounded
    # value. Found live: a real generation's estimated_cost_usd came back this way.
    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional provenance -- which campaign/social_post this generation was made from, set
    # by the frontend. No FK constraint since it can reference either table.
    linked_entity_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AIProviderConnection(Base):
    """An account's own "bring your own model" AI provider credentials (DEC-GRX-026).
    Checked first when resolving which provider a generation call uses; falls back to
    PlatformAIProviderConfig when no active row exists for the account."""

    __tablename__ = "ai_provider_connections"
    __table_args__ = (
        CheckConstraint(_PROVIDER_CHECK, name="ck_ai_provider_connections_provider"),
        # One active BYO connection per account -- an account brings *one* model at a
        # time, unlike email_provider_connections' legitimate per-provider multiplicity.
        Index(
            "ux_ai_provider_connections_active_per_account",
            "account_id",
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
    # Fernet-encrypted at the service layer before insert, per DEC-GRX-026. Nullable --
    # Ollama typically needs no API key. See growixa_api.auth.encryption.
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Required for AZURE_OPENAI/OLLAMA, validated per DEC-GRX-027. Nullable for
    # OPENAI/ANTHROPIC, which use their fixed official base URL.
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PlatformAIProviderConfig(Base):
    """The platform-wide default AI provider (DEC-GRX-026) -- the first DB-backed,
    admin-editable platform setting in this codebase; every prior platform-level setting
    is `.env`-only. Used by any account with no active AIProviderConnection of its own."""

    __tablename__ = "platform_ai_provider_config"
    __table_args__ = (
        CheckConstraint(_PROVIDER_CHECK, name="ck_platform_ai_provider_config_provider"),
        # At most one active platform default: a unique partial index on is_active
        # itself -- every WHERE-matched row has the same (true) value, so Postgres
        # rejects a second one.
        Index(
            "ux_platform_ai_provider_config_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by_platform_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
