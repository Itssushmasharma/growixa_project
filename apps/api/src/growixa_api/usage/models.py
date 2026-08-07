import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class UsageRecord(Base):
    """Foundation usage-metering ledger (DEC-GRX-007). Documented as existing since
    Sprint 1 in DATA_MODEL.md, but never actually built then — created here because
    GRX-EMAIL-004 is genuinely this table's first writer and needs it to exist."""

    __tablename__ = "usage_records"
    __table_args__ = (
        Index("ix_usage_records_operation_type_created_at", "operation_type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_type: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Mapped to the "metadata" column explicitly — "metadata" is a reserved attribute
    # name on SQLAlchemy's declarative Base (Base.metadata is the MetaData registry).
    usage_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
