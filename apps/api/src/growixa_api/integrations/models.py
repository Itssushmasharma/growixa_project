import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class EmailProviderConnection(Base):
    __tablename__ = "email_provider_connections"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('POSTMARK', 'CUSTOM_SMTP')",
            name="ck_email_provider_connections_provider",
        ),
        # DB-enforced "one active connection per provider per account" (GRX-EMAIL-011 /
        # DEC-GRX-016, composite since GRX-SAAS-001) — a partial unique index, not just
        # the app-level deactivate-then-create convention DATA_MODEL.md describes for
        # e.g. company_profile.
        Index(
            "ux_email_provider_connections_active_per_provider",
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
    smtp_host: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False)
    smtp_username: Mapped[str] = mapped_column(Text, nullable=False)
    # Fernet-encrypted at the service layer before insert — never a plaintext column, per
    # DEC-GRX-009. See growixa_api.auth.encryption.
    smtp_password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    # HTTP Basic Auth credentials for the inbound Postmark webhook, per THREAT_MODEL.md's
    # T14 ("stored alongside the provider connection, encrypted at rest"). Auto-generated
    # at connection-creation time; nullable so pre-GRX-EMAIL-005 rows (none exist in
    # practice) don't need a backfill, but the webhook receiver fails closed on NULL.
    webhook_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class SenderIdentity(Base):
    __tablename__ = "sender_identities"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('PENDING', 'VERIFIED', 'FAILED')",
            name="ck_sender_identities_verification_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from email_provider_connection_id's own account_id -- see
    # EmailTemplateVersion's identical note.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email_provider_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_provider_connections.id"), nullable=False
    )
    from_email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    from_name: Mapped[str] = mapped_column(Text, nullable=False)
    reply_to_email: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="PENDING")
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
