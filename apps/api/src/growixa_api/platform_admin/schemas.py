import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class AccountListItemOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    selected_plan_slug: str | None
    created_at: datetime
    user_count: int


class AccountUserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    status: str
    last_login_at: datetime | None


class SecurityEventOut(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    actor_user_id: uuid.UUID | None
    event_metadata: dict[str, Any]
    created_at: datetime


class AccountDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    selected_plan_slug: str | None
    created_at: datetime
    users: list[AccountUserOut]
    security_activity: list[SecurityEventOut]


class UpdateAccountStatusIn(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED", "CLOSED"]


class UsageSummaryItemOut(BaseModel):
    account_id: uuid.UUID
    account_name: str
    operation_type: str
    total_quantity: float
    unit: str


class PlanDistributionItemOut(BaseModel):
    plan_slug: str
    plan_name: str
    account_count: int


class PlatformDashboardSummaryOut(BaseModel):
    total_active_accounts: int
    total_mrr_usd: float
    total_mrr_inr: float
    period_emails_used: int
    period_ai_runs_used: int
    plan_distribution: list[PlanDistributionItemOut]


class CampaignOversightItemOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    account_name: str
    name: str
    status: str
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SupportSessionCreateIn(BaseModel):
    reason: str
    ticket_number: str
    access_level: Literal["READ", "WRITE"] = "READ"


class SupportSessionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    platform_admin_id: uuid.UUID
    reason: str
    ticket_number: str
    access_level: str
    started_at: datetime
    expires_at: datetime
    ended_at: datetime | None


class AuditEventOut(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    actor_user_id: uuid.UUID | None
    event_metadata: dict[str, Any]
    created_at: datetime


class SupportSessionContactOut(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    status: str


class SupportSessionCompanyOut(BaseModel):
    name: str
    website: str | None
    industry: str | None


class SupportSessionOverviewOut(BaseModel):
    session: SupportSessionOut
    company: SupportSessionCompanyOut | None
    contacts: list[SupportSessionContactOut]
    audit_events: list[AuditEventOut]


class SupportSessionContactUpdateIn(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


# --- Billing (GRX-SAAS-006, BILLING_SYSTEM_ARCHITECTURE.md §6) ---


class AccountSubscriptionOverrideIn(BaseModel):
    """At least one of plan_slug/status must be set -- validated in
    billing/services.py's admin_override_subscription, not here, since a Pydantic
    model-level "at least one of" check has no precedent elsewhere in this codebase."""

    plan_slug: str | None = None
    status: Literal["ACTIVE", "PAST_DUE", "HALTED", "CANCELED"] | None = None


class GrantCreditsIn(BaseModel):
    credit_type: Literal["AI_RUNS", "EMAIL_SENDS", "CONTACT_SLOTS", "SOCIAL_POSTS"]
    credits: int


class SubscriptionPlanCreateIn(BaseModel):
    # No Literal restriction (unlike SubscribeIn.plan_slug, GRX-BILL-004) -- creating a
    # genuinely new tier is the point of this route; subscription_plans.slug's CHECK
    # (e3e939e991f4) is a plain format check, not a fixed whitelist.
    slug: str
    name: str
    price_usd: float | None = None
    price_inr: float | None = None
    max_contacts: int | None = None
    max_monthly_emails: int | None = None
    max_monthly_ai_runs: int | None = None
    max_social_accounts: int | None = None
    max_user_seats: int | None = None
    allow_byo_ai_key: bool = False
    allow_byo_smtp: bool = False
    audit_export_enabled: bool = False
    audit_api_enabled: bool = False


class SubscriptionPlanUpdateIn(BaseModel):
    # slug is deliberately not editable -- it's a stable identifier referenced by
    # string literal elsewhere (SubscribeIn's Literal, the Free-plan bootstrap lookup).
    name: str
    price_usd: float | None
    price_inr: float | None
    max_contacts: int | None
    max_monthly_emails: int | None
    max_monthly_ai_runs: int | None
    max_social_accounts: int | None
    max_user_seats: int | None
    allow_byo_ai_key: bool
    allow_byo_smtp: bool
    audit_export_enabled: bool
    audit_api_enabled: bool


class CreditPackCreateIn(BaseModel):
    slug: str
    name: str
    credit_type: Literal["AI_RUNS", "EMAIL_SENDS", "CONTACT_SLOTS", "SOCIAL_POSTS"]
    credits: int
    price_usd: float | None = None
    price_inr: float | None = None
    is_active: bool = True


class CreditPackUpdateIn(BaseModel):
    name: str
    credit_type: Literal["AI_RUNS", "EMAIL_SENDS", "CONTACT_SLOTS", "SOCIAL_POSTS"]
    credits: int
    price_usd: float | None
    price_inr: float | None
    is_active: bool


# --- Coupons (GRX-SAAS-012, BILLING_SYSTEM_ARCHITECTURE.md §7) ---


class CouponCreateIn(BaseModel):
    code: str
    discount_type: Literal["PERCENTAGE", "FIXED_AMOUNT", "CREDIT_GRANT"]
    # PERCENTAGE: 0-100. FIXED_AMOUNT: major currency unit (dollars/rupees), applied to
    # whichever currency the checkout is in. CREDIT_GRANT: number of credits.
    discount_value: float
    # Required (and only meaningful) when discount_type = CREDIT_GRANT.
    credit_type: Literal["AI_RUNS", "EMAIL_SENDS", "CONTACT_SLOTS", "SOCIAL_POSTS"] | None = None
    # None = eligible on every plan/pack (coupons aren't plan-scoped at the checkout
    # layer beyond this optional allowlist).
    applicable_plan_slugs: list[str] | None = None
    max_redemptions: int | None = None
    expires_at: datetime | None = None


class CouponUpdateActiveIn(BaseModel):
    is_active: bool


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    discount_type: str
    discount_value: float
    credit_type: str | None
    applicable_plan_slugs: list[str] | None
    max_redemptions: int | None
    redemption_count: int
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
