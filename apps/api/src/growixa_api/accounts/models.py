import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class Account(Base):
    """A customer account (GRX-SAAS-001 / DEC-GRX-017). The isolation boundary every
    account-owned table's `account_id` column points at — never exposed to end users as a
    "tenant"/"workspace" concept; each user only ever sees "their account"."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')", name="ck_accounts_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="ACTIVE")
    # Nullable until Phase D (GRX-SAAS-004) creates the subscriptions/plans model —
    # column exists now to match DATABASE_SCHEMA.md's eventual shape, per this codebase's
    # established convention (e.g. refresh_tokens.replaced_by_token_id in GRX-AUTH-002).
    plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
