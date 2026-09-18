import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from growixa_api.db import Base

class SMSConnection(Base):
    __tablename__ = "sms_connections"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('TWILIO')",
            name="ck_sms_connections_provider",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    provider: Mapped[str] = mapped_column(Text, nullable=False, server_default="TWILIO")
    account_sid: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Encrypted via growixa_api.auth.encryption
    auth_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    
    # E.164 validated sender number
    sender_number: Mapped[str] = mapped_column(Text, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class SMSCampaign(Base):
    __tablename__ = "sms_campaigns"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'REVIEW', 'CHANGES_REQUESTED', 'APPROVED', 'SCHEDULED', 'DISPATCHING', 'SENDING', 'SENT', 'CANCELLED', 'FAILED')",
            name="ck_sms_campaigns_status",
        ),
        Index("ix_sms_campaigns_status_scheduled_at", "status", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    
    # For SMS, we can just store the text body instead of a template ID initially,
    # as SMS templates are usually freeform unlike WhatsApp strict templates.
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    
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
