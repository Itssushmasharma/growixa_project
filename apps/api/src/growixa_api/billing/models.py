import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base

_CREDIT_TYPE_CHECK = "credit_type IN ('AI_RUNS', 'EMAIL_SENDS', 'CONTACT_SLOTS', 'SOCIAL_POSTS')"


class SubscriptionPlan(Base):
    """The platform-wide plan catalog -- one row per tier, editable by a platform admin
    (platform.billing.manage) without a redeploy, same DB-backed-admin-editable-setting
    pattern PlatformAIProviderConfig established in Slice 6 (DEC-GRX-029/030)."""

    __tablename__ = "subscription_plans"
    __table_args__ = (
        CheckConstraint(
            "slug IN ('free', 'starter', 'pro', 'enterprise')", name="ck_subscription_plans_slug"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # NULL for Enterprise -- contact-sales, no fixed self-serve price (DEC-GRX-030 point 4).
    price_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # NULL = unlimited on every quota column below.
    max_contacts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_monthly_emails: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_monthly_ai_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_social_accounts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_user_seats: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_byo_ai_key: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    allow_byo_smtp: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    audit_export_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    audit_api_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # The Razorpay Plan a new subscription attaches to (GRX-BILL-004). NULL for
    # Free/Enterprise, neither of which self-serve-checkouts through Razorpay.
    razorpay_plan_id_usd: Mapped[str | None] = mapped_column(Text, nullable=True)
    razorpay_plan_id_inr: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AccountSubscription(Base):
    """Exactly one row per account -- created automatically at registration
    (BILLING_SYSTEM_ARCHITECTURE.md §3.4), never zero, never more than one. The running
    period_email_used/period_ai_used counters here are what the atomic quota evaluator
    (GRX-BILL-005) locks with SELECT ... FOR UPDATE before reading or writing."""

    __tablename__ = "account_subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'PAST_DUE', 'CANCELED', 'HALTED')",
            name="ck_account_subscriptions_status",
        ),
        CheckConstraint("currency IN ('USD', 'INR')", name="ck_account_subscriptions_currency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_email_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    period_ai_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # NULL for an account on an admin-assigned plan with no real Razorpay object (most
    # Enterprise accounts, or any manual override via GRX-SAAS-006).
    razorpay_customer_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    razorpay_subscription_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    set_by_platform_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AccountCreditBalance(Base):
    """The number the quota evaluator actually reads once the monthly plan allowance is
    exhausted -- one running, non-expiring balance per account per credit type
    (DEC-GRX-030: credits never expire, no per-purchase-batch FIFO). Never mutated
    except via the atomic UPDATE ... WHERE remaining_credits >= :needed the evaluator
    runs (GRX-BILL-005) or a purchase/grant crediting it (GRX-BILL-003/GRX-SAAS-006)."""

    __tablename__ = "account_credit_balances"
    __table_args__ = (
        CheckConstraint(_CREDIT_TYPE_CHECK, name="ck_account_credit_balances_credit_type"),
        UniqueConstraint(
            "account_id", "credit_type", name="ux_account_credit_balances_account_type"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    credit_type: Mapped[str] = mapped_column(Text, nullable=False)
    remaining_credits: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AccountCreditPurchase(Base):
    """Receipt/audit history of individual top-up purchases and admin-granted credits.
    Never read by the quota evaluator -- purely a record; AccountCreditBalance.
    remaining_credits is the only value that gates anything at request time."""

    __tablename__ = "account_credit_purchases"
    __table_args__ = (
        CheckConstraint(_CREDIT_TYPE_CHECK, name="ck_account_credit_purchases_credit_type"),
        Index("ix_account_credit_purchases_account_id", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    credit_type: Mapped[str] = mapped_column(Text, nullable=False)
    credits_added: Mapped[int] = mapped_column(Integer, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Unique when set -- the webhook-replay idempotency guard (THREAT_MODEL.md T61).
    # NULL for an admin-granted credit rather than a real purchase (GRX-SAAS-006).
    razorpay_payment_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    granted_by_platform_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), nullable=True
    )


class CouponCode(Base):
    """Platform-admin-managed discount/free-credit code (GRX-SAAS-012, DEC-GRX-030
    point 6)."""

    __tablename__ = "coupon_codes"
    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT', 'CREDIT_GRANT')",
            name="ck_coupon_codes_discount_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(Text, nullable=False)
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # Only set when discount_type = CREDIT_GRANT.
    credit_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    # NULL = all plans eligible.
    applicable_plan_slugs: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redemption_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by_platform_admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_admins.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CouponRedemption(Base):
    """One row per use -- the unique constraint below is the one-redemption-per-account
    enforcement (THREAT_MODEL.md T65), not just a convenience index."""

    __tablename__ = "coupon_redemptions"
    __table_args__ = (
        UniqueConstraint("coupon_code_id", "account_id", name="ux_coupon_redemptions_code_account"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coupon_codes.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
