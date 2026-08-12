import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class SocialConnection(Base):
    __tablename__ = "social_connections"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('INSTAGRAM_BUSINESS')",
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
    ig_business_account_id: Mapped[str] = mapped_column(Text, nullable=False)
    ig_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    facebook_page_id: Mapped[str] = mapped_column(Text, nullable=False)
    # Fernet-encrypted at the service layer before insert, per DEC-GRX-025. See
    # growixa_api.auth.encryption.
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
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
