import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class RazorpayWebhookPayload(BaseModel):
    """Deliberately permissive, same convention as PostmarkWebhookPayload
    (email_delivery/schemas.py) -- Razorpay's `payload` shape varies significantly by
    `event` type (subscription.* events nest a `subscription` entity, payment.captured
    nests a `payment` entity). Only `event` itself is required; everything else is
    read defensively in services.py rather than strictly typed here."""

    model_config = ConfigDict(extra="allow")

    event: str
    payload: dict[str, Any] = {}


class SubscribeIn(BaseModel):
    # No "free" (default at registration, no checkout needed) or "enterprise"
    # (contact-sales, platform-admin-activated only, DEC-GRX-030 point 4).
    plan_slug: Literal["starter", "pro"]
    currency: Literal["USD", "INR"]


class SubscribeOut(BaseModel):
    razorpay_subscription_id: str
    # The frontend's Checkout.js widget needs the public key alongside the
    # subscription id -- never the secret, which never leaves the server.
    razorpay_key_id: str


class TopUpIn(BaseModel):
    pack_slug: str
    currency: Literal["USD", "INR"]


class TopUpOut(BaseModel):
    razorpay_order_id: str
    razorpay_key_id: str
    amount_smallest_unit: int
    currency: Literal["USD", "INR"]


class SubscriptionPlanOut(BaseModel):
    """The catalog shape a customer's billing page picks an upgrade/downgrade from --
    same fields as SubscriptionPlan minus the Razorpay Plan ids, which are an internal
    checkout-time implementation detail the frontend has no use for (GRX-BILL-007)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
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


class CreditPackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    credit_type: str
    credits: int
    price_usd: float | None
    price_inr: float | None
    # Every customer-facing GET /billing/credit-packs response is already filtered to
    # is_active rows only, so this was always true there and easy to omit -- but the
    # platform-admin catalog view (GRX-SAAS-006) lists *every* pack including
    # deactivated ones, and needs this field to tell them apart.
    is_active: bool


class CreditBalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    credit_type: str
    remaining_credits: int


class AccountSubscriptionOut(BaseModel):
    plan: SubscriptionPlanOut
    status: str
    currency: Literal["USD", "INR"]
    current_period_start: datetime
    current_period_end: datetime
    period_email_used: int
    period_ai_used: int
    credit_balances: list[CreditBalanceOut]
