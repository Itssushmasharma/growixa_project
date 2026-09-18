import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from growixa_api.db import Base

class WhatsAppConnection(Base):
    __tablename__ = "whatsapp_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Meta WhatsApp Business Account ID
    waba_id: Mapped[str] = mapped_column(Text, nullable=False)
    # The actual phone number ID mapped to the WABA
    phone_number_id: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Encrypted via growixa_api.auth.encryption
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_verify_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"
    __table_args__ = (
        CheckConstraint(
            "status IN ('APPROVED', 'PENDING', 'REJECTED')",
            name="ck_whatsapp_templates_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    name: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="PENDING")
    
    # JSON array for components: BODY, HEADER, BUTTONS
    components: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WhatsAppCampaign(Base):
    __tablename__ = "whatsapp_campaigns"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'REVIEW', 'CHANGES_REQUESTED', 'APPROVED', 'SCHEDULED', 'DISPATCHING', 'SENDING', 'SENT', 'CANCELLED', 'FAILED')",
            name="ck_whatsapp_campaigns_status",
        ),
        Index("ix_whatsapp_campaigns_status_scheduled_at", "status", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("whatsapp_templates.id"), nullable=True
    )
    
    recipient_type: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("segments.id"), nullable=True
    )
    recipient_list_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contact_lists.id"), nullable=True
    )
    
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="DRAFT")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
