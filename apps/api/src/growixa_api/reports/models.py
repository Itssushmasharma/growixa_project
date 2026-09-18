import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from growixa_api.db import Base

class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('DAILY', 'WEEKLY', 'MONTHLY')",
            name="ck_scheduled_reports_frequency",
        ),
        CheckConstraint(
            "report_type IN ('CLIENT', 'CHANNEL', 'CAMPAIGN', 'ACCOUNT_OVERVIEW')",
            name="ck_scheduled_reports_report_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'PAUSED')",
            name="ck_scheduled_reports_status",
        ),
        Index("ix_scheduled_reports_next_run_at", "next_run_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    name: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(Text, nullable=False)
    report_type: Mapped[str] = mapped_column(Text, nullable=False)
    
    recipient_emails: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="ACTIVE")
    
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
