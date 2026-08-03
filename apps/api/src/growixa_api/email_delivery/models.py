import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class MessageDelivery(Base):
    __tablename__ = "message_deliveries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED', 'SENT', 'DELIVERED', 'BOUNCED', 'COMPLAINED', 'FAILED')",
            name="ck_message_deliveries_status",
        ),
        Index("ix_message_deliveries_provider_message_id", "provider_message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaign_recipients.id", ondelete="CASCADE"), nullable=False
    )
    provider_message_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="QUEUED")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bounced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"
    __table_args__ = (Index("ix_delivery_attempts_message_delivery_id", "message_delivery_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message_deliveries.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
