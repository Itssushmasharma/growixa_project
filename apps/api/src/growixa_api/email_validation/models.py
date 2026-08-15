import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base

# Only CLEAROUT is actually implemented (an adapter must exist in providers/ before a
# value is added here) -- widen this CHECK in a follow-up migration when a second
# vendor's adapter actually ships (GRX-SAAS-016 ad hoc, follow-up pass), same
# extend-when-built discipline as every other provider-CHECK column in this codebase.
_PROVIDER_CHECK = "provider IN ('CLEAROUT')"


class PlatformEmailValidationProviderConfig(Base):
    """The platform-wide real-time mailbox-verification vendor (GRX-SAAS-016 follow-up
    pass) -- same DB-backed, admin-editable-without-redeploy, "at most one active row"
    pattern as PlatformAIProviderConfig/PlatformEmailProviderConfig. Deliberately
    platform-level only, no per-account bring-your-own: Growixa buys verification
    credits wholesale from the configured vendor and meters usage by the account's own
    plan tier (paid plans only), not a customer-supplied API key."""

    __tablename__ = "platform_email_validation_provider_config"
    __table_args__ = (
        CheckConstraint(
            _PROVIDER_CHECK, name="ck_platform_email_validation_provider_config_provider"
        ),
        Index(
            "ux_platform_email_validation_provider_config_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    # Every currently-supported provider requires a key (unlike AI's Ollama case), so
    # this stays NOT NULL rather than mirroring AIProviderConnection's nullable column.
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
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
