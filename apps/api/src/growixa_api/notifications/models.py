import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class PlatformEmailProviderConfig(Base):
    """The platform-wide email provider used for system/transactional email
    (registration verification today) -- same admin-editable-without-redeploy pattern
    as PlatformAIProviderConfig, and the same provider vocabulary/SMTP transport as the
    account-level EmailProviderConnection (POSTMARK is just SMTP pointed at Postmark's
    relay with the server token as both username and password -- no separate code path
    exists for it anywhere in this codebase, so none is added here either). Resolved by
    notifications/services.py; falls back to the legacy .env-only PLATFORM_SMTP_* config
    when no active row exists, so an existing deployment isn't broken by this table's
    introduction."""

    __tablename__ = "platform_email_provider_config"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('POSTMARK', 'CUSTOM_SMTP')",
            name="ck_platform_email_provider_config_provider",
        ),
        # At most one active platform default -- same unique-partial-index shape as
        # platform_ai_provider_config.
        Index(
            "ux_platform_email_provider_config_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_host: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False)
    smtp_username: Mapped[str] = mapped_column(Text, nullable=False)
    # Fernet-encrypted at the service layer before insert, per DEC-GRX-009 -- same
    # convention as email_provider_connections.smtp_password_encrypted.
    smtp_password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    from_email: Mapped[str] = mapped_column(Text, nullable=False)
    from_name: Mapped[str] = mapped_column(Text, nullable=False)
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
