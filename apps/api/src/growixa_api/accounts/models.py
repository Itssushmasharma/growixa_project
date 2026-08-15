import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text
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
        CheckConstraint(
            "selected_plan_slug IN ('free', 'starter', 'pro')",
            name="ck_accounts_selected_plan_slug",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="ACTIVE")
    # GRX-SAAS-003 Phase C: the self-service plan picked at registration -- recorded
    # only, no FK, purely a UX/marketing intent signal (see DEC-GRX-019). Real
    # entitlement lives in billing.models.AccountSubscription (GRX-BILL-002), created
    # unconditionally on the `free` plan regardless of what's recorded here -- an
    # account only actually changes plan via a real Razorpay checkout or a platform
    # admin override, never by what it selected at signup.
    selected_plan_slug: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AccountVerificationToken(Base):
    """One-time email verification for a self-registered account's first user
    (GRX-SAAS-003 Phase C) -- structurally identical to `password_reset_tokens`."""

    __tablename__ = "account_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
