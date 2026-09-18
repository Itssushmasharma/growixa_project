import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from growixa_api.db import Base

class RawProviderEvent(Base):
    __tablename__ = "raw_provider_events"
    __table_args__ = (
        Index("ix_raw_provider_events_account_provider", "account_id", "provider"),
        Index("ix_raw_provider_events_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    provider: Mapped[str] = mapped_column(Text, nullable=False) # e.g. META, TWILIO, SENDGRID
    event_type: Mapped[str] = mapped_column(Text, nullable=False) # e.g. message_delivered, lead_created
    
    payload_jsonb: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('CAMPAIGN', 'SOCIAL_POST', 'CRM', 'CHANNEL')",
            name="ck_metric_snapshots_entity_type",
        ),
        # Ensure we only have one snapshot per entity per date
        Index(
            "ux_metric_snapshots_entity_date",
            "account_id",
            "entity_type",
            "entity_id",
            "date",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    # The ID of the Campaign, SocialPost, or a generic Channel ID
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    metrics_jsonb: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
