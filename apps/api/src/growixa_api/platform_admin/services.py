import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import list_events, record_event
from growixa_api.auth.services import revoke_all_active_sessions
from growixa_api.billing.models import (
    AccountCreditBalance,
    AccountSubscription,
    CouponCode,
    CreditPack,
)
from growixa_api.billing.models import SubscriptionPlan as SubscriptionPlanModel
from growixa_api.billing.services import (
    CouponCodeAlreadyExistsError,
    CreditPackSlugAlreadyExistsError,
    PlanSlugAlreadyExistsError,
    get_billing_overview,
)
from growixa_api.billing.services import (
    CouponMissingCreditTypeError as BillingCouponMissingCreditTypeError,
)
from growixa_api.billing.services import CouponNotFoundError as BillingCouponNotFoundError
from growixa_api.billing.services import CreditPackNotFoundError as BillingCreditPackNotFoundError
from growixa_api.billing.services import NoOverrideFieldsProvidedError as BillingNoFieldsError
from growixa_api.billing.services import PlanNotFoundError as BillingPlanNotFoundError
from growixa_api.billing.services import (
    admin_create_coupon as billing_create_coupon,
)
from growixa_api.billing.services import admin_create_credit_pack as billing_create_credit_pack
from growixa_api.billing.services import admin_create_plan as billing_create_plan
from growixa_api.billing.services import admin_grant_credits as billing_grant_credits
from growixa_api.billing.services import (
    admin_override_subscription as billing_override_subscription,
)
from growixa_api.billing.services import admin_set_coupon_active as billing_set_coupon_active
from growixa_api.billing.services import admin_update_credit_pack as billing_update_credit_pack
from growixa_api.billing.services import admin_update_plan as billing_update_plan
from growixa_api.billing.services import list_coupon_catalog as billing_list_coupon_catalog
from growixa_api.campaigns.models import Campaign
from growixa_api.campaigns.services import CampaignNotCancellableError, cancel_campaign
from growixa_api.campaigns.services import CampaignNotFoundError as CampaignRowNotFoundError
from growixa_api.company.models import CompanyProfile
from growixa_api.company.services import get_profile as get_company_profile
from growixa_api.config import get_settings
from growixa_api.contacts.services import ContactSnapshot
from growixa_api.contacts.services import list_contacts_with_fields as list_contacts_service
from growixa_api.contacts.services import update_contact as update_contact_service
from growixa_api.platform_admin.models import SupportSession
from growixa_api.platform_admin.repositories import (
    count_active_accounts,
    count_active_subscriptions,
    count_subscriptions_canceled_since,
    count_users_by_account,
    create_support_session,
    get_account_by_id,
    get_campaign_by_id,
    get_mrr_totals,
    get_period_usage_totals,
    get_plan_distribution,
    get_support_session_by_id,
    list_accounts,
    list_campaigns_by_status,
    list_support_sessions_for_account,
    list_usage_summary,
)
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.platform_auth.repositories import platform_admin_has_permission
from growixa_api.users.models import User
from growixa_api.users.repositories import list_users

# GRX-SAAS-008 / DEC-GRX-021 point 2: "queued" (not yet dispatched or in-flight) plus
# FAILED -- the two states oversight actually cares about. SENT/CANCELLED/DRAFT are
# excluded: SENT/CANCELLED are resolved, DRAFT hasn't been scheduled by its owner yet.
_OVERSIGHT_STATUSES = ("SCHEDULED", "DISPATCHING", "SENDING", "FAILED")

# "Login/security activity" (GRX-SAAS-005) is a filtered view over the existing
# audit_logs table, not a new table or a raw dump -- a busy account's audit_logs also
# carries non-security business events (contact edits, campaign sends, ...) that would
# bury the actual signal. See DEC-GRX-020 point 4.
_SECURITY_ACTIONS = frozenset(
    {
        "user.login",
        "user.login_failed",
        "user.logout",
        "session.revoked",
        "user.password_reset_requested",
        "user.password_reset_completed",
        "role.changed",
        "account.registered",
        "user.email_verified",
        "account.suspended",
        "account.reactivated",
        "account.closed",
    }
)

_STATUS_TO_ACTION = {
    "ACTIVE": "account.reactivated",
    "SUSPENDED": "account.suspended",
    "CLOSED": "account.closed",
}


class AccountNotFoundError(Exception):
    """The target account id doesn't match any existing account."""


class CampaignNotFoundError(Exception):
    """The target campaign id doesn't match any existing campaign."""


class CampaignNotPausableError(Exception):
    """The campaign is not in a state that can be paused (DRAFT/SCHEDULED only) --
    mirrors campaigns/services.py's own CampaignNotCancellableError, since pausing
    reuses that exact state transition (DEC-GRX-021 point 2)."""


class SupportSessionWriteNotPermittedError(Exception):
    """Requested access_level=WRITE but the acting admin lacks
    platform.support_session.write (DEC-GRX-022 point 2 -- the "separate permission
    gate for write access")."""


class SupportSessionNotFoundError(Exception):
    """The target support_session id doesn't match any existing session."""


class SupportSessionAccessDeniedError(Exception):
    """The session exists but belongs to a different platform admin
    (THREAT_MODEL.md T38 -- a session id alone is never sufficient)."""


class SupportSessionExpiredError(Exception):
    """The session has ended or its expires_at has passed (THREAT_MODEL.md T39)."""


class SupportSessionWriteGateError(Exception):
    """The write action was attempted through a READ-level session, or by an admin
    who never held platform.support_session.write (THREAT_MODEL.md T40 -- two
    independent checks, either one alone blocks it)."""


class SubscriptionOverrideMissingFieldsError(Exception):
    """Neither plan_slug nor status was provided to the subscription-override route
    (GRX-SAAS-006) -- there's nothing to change."""


class SubscriptionPlanNotFoundError(Exception):
    """The target plan id/slug doesn't match any existing plan."""


class SubscriptionPlanSlugConflictError(Exception):
    """A plan with this slug already exists."""


class CreditPackNotFoundError(Exception):
    """The target credit pack id doesn't match any existing pack."""


class CreditPackSlugConflictError(Exception):
    """A credit pack with this slug already exists."""


class CouponCodeConflictError(Exception):
    """A coupon with this code already exists."""


class CouponNotFoundError(Exception):
    """The target coupon id doesn't match any existing coupon."""


class CouponMissingCreditTypeError(Exception):
    """A CREDIT_GRANT coupon was created without credit_type set."""


async def list_accounts_with_user_counts(session: AsyncSession) -> list[tuple[Account, int]]:
    accounts = await list_accounts(session)
    counts = await count_users_by_account(session)
    return [(account, counts.get(account.id, 0)) for account in accounts]


async def get_account_detail(
    session: AsyncSession, *, account_id: uuid.UUID
) -> tuple[Account, list[User], list[AuditLog]]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    users = await list_users(session, account_id=account_id)
    events = await list_events(session, account_id=account_id, limit=100)
    security_events = [event for event in events if event.action in _SECURITY_ACTIONS]
    return account, list(users), security_events


async def update_account_status(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    status: str,
) -> tuple[Account, int]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    account.status = status
    users = await list_users(session, account_id=account_id)

    # Per DEC-GRX-020: a suspend/close takes effect immediately, not just at each user's
    # next token refresh -- mirrors GRX-USER-002's existing per-user disable behavior,
    # now applied to every user in the account at once.
    if status in ("SUSPENDED", "CLOSED"):
        for user in users:
            await revoke_all_active_sessions(session, user.id, reason=f"account_{status.lower()}")

    # audit_logs.actor_user_id FKs to users.id and cannot reference platform_admins.id --
    # per DEC-GRX-020, the acting admin is recorded in metadata instead, same
    # actor_user_id=None shape login() already uses for an unresolvable actor.
    admin = await session.get(PlatformAdmin, platform_admin_id)
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=None,
        action=_STATUS_TO_ACTION[status],
        entity_type="account",
        entity_id=account_id,
        metadata={
            "platform_admin_id": str(platform_admin_id),
            "platform_admin_email": admin.email if admin is not None else None,
        },
    )
    await session.commit()

    return account, len(users)


async def list_usage_summary_rows(
    session: AsyncSession,
) -> Sequence[Row[tuple[uuid.UUID, str, str, float, str]]]:
    return await list_usage_summary(session)


async def get_platform_dashboard_summary(
    session: AsyncSession,
) -> tuple[int, float, float, int, int, Sequence[Row[tuple[str, str, int]]]]:
    total_active_accounts = await count_active_accounts(session)
    mrr_usd, mrr_inr = await get_mrr_totals(session)
    emails_used, ai_runs_used = await get_period_usage_totals(session)
    distribution_rows = await get_plan_distribution(session)
    return total_active_accounts, mrr_usd, mrr_inr, emails_used, ai_runs_used, distribution_rows


@dataclass(frozen=True)
class FinancialMetrics:
    mrr_by_currency: dict[str, float]
    arr_by_currency: dict[str, float]
    active_subscription_count: int
    churned_last_30_days: int
    churn_rate_percent: float


CHURN_WINDOW_DAYS = 30


async def get_financial_metrics(session: AsyncSession) -> FinancialMetrics:
    """MRR/ARR/churn for the platform-admin financial dashboard (`GRX-SAAS-009`).

    MRR reuses `get_mrr_totals` -- the exact same ACTIVE-only, per-currency
    definition already shown on the platform overview page (`get_platform_dashboard_
    summary`). Deliberately not a second, differently-scoped MRR calculation: two
    different "MRR" numbers on two different admin pages would undermine trust in
    both. ARR = MRR x 12; this project bills monthly only (no annual plans exist), so
    ARR is a straightforward annualization, not a separately-billed figure.

    Top-up/credit-pack revenue is deliberately NOT included here: `account_credit_
    purchases` records `credits_added` but not the amount paid or currency, and there
    is no FK back to which `credit_pack`/price was actually purchased -- computing a
    dollar figure would mean guessing at a mapping the schema doesn't capture. That's
    a real data-model gap, not a rounding error, and needs its own schema decision
    (e.g. a `credit_pack_id`/`amount_paid`/`currency` column on the purchase row)
    rather than an approximation here.

    Churn: there is no dedicated subscription-status-change history table, so this
    uses `updated_at` on a `CANCELED` row as a proxy for "when it churned" --
    `churned_last_30_days` = count of subscriptions that became `CANCELED` in the
    trailing 30 days. `churn_rate_percent` = churned / (currently ACTIVE + churned),
    i.e. churned as a fraction of the accounts that were billable at the start of the
    window (approximated as today's active count plus the ones that just left it) --
    a standard, simple churn-rate definition, not a precise cohort analysis.
    """
    mrr_usd, mrr_inr = await get_mrr_totals(session)
    mrr = {"USD": mrr_usd, "INR": mrr_inr}
    arr = {currency: value * 12 for currency, value in mrr.items()}

    active_count = await count_active_subscriptions(session)
    since = datetime.now(UTC) - timedelta(days=CHURN_WINDOW_DAYS)
    churned = await count_subscriptions_canceled_since(session, since=since)
    base = active_count + churned
    churn_rate = (churned / base * 100) if base > 0 else 0.0

    return FinancialMetrics(
        mrr_by_currency=mrr,
        arr_by_currency=arr,
        active_subscription_count=active_count,
        churned_last_30_days=churned,
        churn_rate_percent=round(churn_rate, 2),
    )


async def list_campaigns_for_oversight(
    session: AsyncSession,
) -> Sequence[Row[tuple[Campaign, str]]]:
    return await list_campaigns_by_status(session, statuses=_OVERSIGHT_STATUSES)


async def pause_campaign(
    session: AsyncSession, *, campaign_id: uuid.UUID, platform_admin_id: uuid.UUID
) -> tuple[Campaign, str]:
    """Reuses campaigns/services.py's own cancel_campaign transition
    (DRAFT/SCHEDULED -> CANCELLED) -- per DEC-GRX-021, a platform admin's "pause" and a
    customer's "cancel" are the same action, just invoked by a different actor."""
    campaign = await get_campaign_by_id(session, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError

    try:
        campaign = await cancel_campaign(session, campaign.account_id, campaign_id)
    except CampaignRowNotFoundError as exc:
        raise CampaignNotFoundError from exc
    except CampaignNotCancellableError as exc:
        raise CampaignNotPausableError(str(exc)) from exc

    account = await get_account_by_id(session, campaign.account_id)
    account_name = account.name if account is not None else ""

    # Same actor_user_id=None + metadata attribution as DEC-GRX-020, applied to a
    # second action type (DEC-GRX-021 point 4).
    admin = await session.get(PlatformAdmin, platform_admin_id)
    await record_event(
        session,
        account_id=campaign.account_id,
        actor_user_id=None,
        action="campaign.paused",
        entity_type="campaign",
        entity_id=campaign.id,
        metadata={
            "platform_admin_id": str(platform_admin_id),
            "platform_admin_email": admin.email if admin is not None else None,
        },
    )
    await session.commit()

    return campaign, account_name


async def _admin_metadata(session: AsyncSession, platform_admin_id: uuid.UUID) -> dict[str, object]:
    admin = await session.get(PlatformAdmin, platform_admin_id)
    return {
        "platform_admin_id": str(platform_admin_id),
        "platform_admin_email": admin.email if admin is not None else None,
    }


async def start_support_session(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    reason: str,
    ticket_number: str,
    access_level: str,
) -> SupportSession:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    if access_level == "WRITE" and not await platform_admin_has_permission(
        session, platform_admin_id, "platform.support_session.write"
    ):
        raise SupportSessionWriteNotPermittedError

    expires_at = datetime.now(UTC) + timedelta(minutes=get_settings().support_session_ttl_minutes)
    support_session = await create_support_session(
        session,
        account_id=account_id,
        platform_admin_id=platform_admin_id,
        reason=reason,
        ticket_number=ticket_number,
        access_level=access_level,
        expires_at=expires_at,
    )

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata.update(
        {"reason": reason, "ticket_number": ticket_number, "access_level": access_level}
    )
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=None,
        action="support_session.started",
        entity_type="support_session",
        entity_id=support_session.id,
        metadata=metadata,
    )
    await session.commit()
    await session.refresh(support_session)
    return support_session


async def list_support_sessions_for_account_service(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SupportSession]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError
    return await list_support_sessions_for_account(session, account_id)


async def _load_owned_active_session(
    session: AsyncSession, *, support_session_id: uuid.UUID, platform_admin_id: uuid.UUID
) -> SupportSession:
    """Shared by every route that acts *through* an existing session (overview read,
    the gated write action, ending early) -- THREAT_MODEL.md T38/T39 in one place
    rather than re-checked ad hoc per caller."""
    support_session = await get_support_session_by_id(session, support_session_id)
    if support_session is None:
        raise SupportSessionNotFoundError
    if support_session.platform_admin_id != platform_admin_id:
        raise SupportSessionAccessDeniedError
    if support_session.ended_at is not None or support_session.expires_at <= datetime.now(UTC):
        raise SupportSessionExpiredError
    return support_session


async def end_support_session(
    session: AsyncSession, *, support_session_id: uuid.UUID, platform_admin_id: uuid.UUID
) -> SupportSession:
    support_session = await _load_owned_active_session(
        session, support_session_id=support_session_id, platform_admin_id=platform_admin_id
    )
    support_session.ended_at = datetime.now(UTC)

    metadata = await _admin_metadata(session, platform_admin_id)
    await record_event(
        session,
        account_id=support_session.account_id,
        actor_user_id=None,
        action="support_session.ended",
        entity_type="support_session",
        entity_id=support_session.id,
        metadata=metadata,
    )
    await session.commit()
    await session.refresh(support_session)
    return support_session


async def get_support_session_overview(
    session: AsyncSession, *, support_session_id: uuid.UUID, platform_admin_id: uuid.UUID
) -> tuple[SupportSession, CompanyProfile | None, list[ContactSnapshot], Sequence[AuditLog]]:
    support_session = await _load_owned_active_session(
        session, support_session_id=support_session_id, platform_admin_id=platform_admin_id
    )
    company = await get_company_profile(session, support_session.account_id)
    contacts = await list_contacts_service(session, support_session.account_id)
    # Full operational trail, not GRX-SAAS-005's security-action-filtered subset --
    # support needs day-to-day context, not just security events (DEC-GRX-022 point 3).
    audit_events = await list_events(session, account_id=support_session.account_id, limit=100)
    return support_session, company, contacts, audit_events


async def update_contact_via_support_session(
    session: AsyncSession,
    *,
    support_session_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    contact_id: uuid.UUID,
    email: str | None,
    first_name: str | None,
    last_name: str | None,
    phone: str | None,
) -> ContactSnapshot:
    support_session = await _load_owned_active_session(
        session, support_session_id=support_session_id, platform_admin_id=platform_admin_id
    )
    if support_session.access_level != "WRITE":
        raise SupportSessionWriteGateError

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["support_session_id"] = str(support_session_id)

    return await update_contact_service(
        session,
        account_id=support_session.account_id,
        actor_id=None,
        contact_id=contact_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        custom_fields=None,
        audit_metadata=metadata,
    )


# --- Billing (GRX-SAAS-006, BILLING_SYSTEM_ARCHITECTURE.md §6) ---
#
# Every write below delegates the actual table mutation to billing/services.py's own
# admin_* functions (MODULE_BOUNDARIES.md: platform_admin calls the owning module's
# services, never writes its tables directly) and adds one audit-log entry in the same
# transaction, mirroring update_account_status/pause_campaign above exactly.


async def get_account_subscription_overview(
    session: AsyncSession, *, account_id: uuid.UUID
) -> tuple[AccountSubscription, SubscriptionPlanModel, Sequence[AccountCreditBalance]]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError
    return await get_billing_overview(session, account_id)


async def override_account_subscription(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    plan_slug: str | None,
    status: str | None,
) -> tuple[AccountSubscription, SubscriptionPlanModel]:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    try:
        subscription, plan = await billing_override_subscription(
            session,
            account_id=account_id,
            plan_slug=plan_slug,
            status=status,
            platform_admin_id=platform_admin_id,
        )
    except BillingNoFieldsError as exc:
        raise SubscriptionOverrideMissingFieldsError from exc
    except BillingPlanNotFoundError as exc:
        raise SubscriptionPlanNotFoundError(str(exc)) from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata.update({"plan_slug": plan_slug, "status": status})
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=None,
        action="account.subscription_overridden",
        entity_type="account_subscription",
        entity_id=subscription.id,
        metadata=metadata,
    )
    await session.commit()
    return subscription, plan


async def grant_account_credits(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    credit_type: str,
    credits: int,
) -> AccountCreditBalance:
    account = await get_account_by_id(session, account_id)
    if account is None:
        raise AccountNotFoundError

    balance = await billing_grant_credits(
        session,
        account_id=account_id,
        credit_type=credit_type,
        credits=credits,
        platform_admin_id=platform_admin_id,
    )

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata.update({"credit_type": credit_type, "credits": credits})
    await record_event(
        session,
        account_id=account_id,
        actor_user_id=None,
        action="account.credits_granted",
        entity_type="account_credit_balance",
        entity_id=account_id,
        metadata=metadata,
    )
    await session.commit()
    return balance


async def create_subscription_plan(
    session: AsyncSession, *, platform_admin_id: uuid.UUID, fields: dict[str, object]
) -> SubscriptionPlanModel:
    try:
        plan = await billing_create_plan(session, fields=fields)
    except PlanSlugAlreadyExistsError as exc:
        raise SubscriptionPlanSlugConflictError(str(exc)) from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["slug"] = fields["slug"]
    await record_event(
        session,
        account_id=None,
        actor_user_id=None,
        action="subscription_plan.created",
        entity_type="subscription_plan",
        entity_id=plan.id,
        metadata=metadata,
    )
    await session.commit()
    return plan


async def update_subscription_plan(
    session: AsyncSession,
    *,
    plan_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    fields: dict[str, object],
) -> SubscriptionPlanModel:
    try:
        plan = await billing_update_plan(session, plan_id=plan_id, fields=fields)
    except BillingPlanNotFoundError as exc:
        raise SubscriptionPlanNotFoundError(str(exc)) from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["fields"] = fields
    await record_event(
        session,
        account_id=None,
        actor_user_id=None,
        action="subscription_plan.updated",
        entity_type="subscription_plan",
        entity_id=plan.id,
        metadata=metadata,
    )
    await session.commit()
    return plan


async def create_credit_pack_catalog_entry(
    session: AsyncSession, *, platform_admin_id: uuid.UUID, fields: dict[str, object]
) -> CreditPack:
    try:
        pack = await billing_create_credit_pack(session, fields=fields)
    except CreditPackSlugAlreadyExistsError as exc:
        raise CreditPackSlugConflictError(str(exc)) from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["slug"] = fields["slug"]
    await record_event(
        session,
        account_id=None,
        actor_user_id=None,
        action="credit_pack.created",
        entity_type="credit_pack",
        entity_id=pack.id,
        metadata=metadata,
    )
    await session.commit()
    return pack


async def update_credit_pack_catalog_entry(
    session: AsyncSession,
    *,
    pack_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    fields: dict[str, object],
) -> CreditPack:
    try:
        pack = await billing_update_credit_pack(session, pack_id=pack_id, fields=fields)
    except BillingCreditPackNotFoundError as exc:
        raise CreditPackNotFoundError(str(exc)) from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["fields"] = fields
    await record_event(
        session,
        account_id=None,
        actor_user_id=None,
        action="credit_pack.updated",
        entity_type="credit_pack",
        entity_id=pack.id,
        metadata=metadata,
    )
    await session.commit()
    return pack


# --- Coupons (GRX-SAAS-012, BILLING_SYSTEM_ARCHITECTURE.md §7.2) ---


async def list_coupons_for_admin(session: AsyncSession) -> Sequence[CouponCode]:
    return await billing_list_coupon_catalog(session)


async def create_coupon(
    session: AsyncSession, *, platform_admin_id: uuid.UUID, fields: dict[str, object]
) -> CouponCode:
    try:
        coupon = await billing_create_coupon(
            session, created_by_platform_admin_id=platform_admin_id, fields=fields
        )
    except CouponCodeAlreadyExistsError as exc:
        raise CouponCodeConflictError(str(exc)) from exc
    except BillingCouponMissingCreditTypeError as exc:
        raise CouponMissingCreditTypeError from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["code"] = fields["code"]
    await record_event(
        session,
        account_id=None,
        actor_user_id=None,
        action="coupon.created",
        entity_type="coupon_code",
        entity_id=coupon.id,
        metadata=metadata,
    )
    await session.commit()
    return coupon


async def set_coupon_active(
    session: AsyncSession, *, coupon_id: uuid.UUID, platform_admin_id: uuid.UUID, is_active: bool
) -> CouponCode:
    try:
        coupon = await billing_set_coupon_active(session, coupon_id=coupon_id, is_active=is_active)
    except BillingCouponNotFoundError as exc:
        raise CouponNotFoundError(str(exc)) from exc

    metadata = await _admin_metadata(session, platform_admin_id)
    metadata["is_active"] = is_active
    await record_event(
        session,
        account_id=None,
        actor_user_id=None,
        action="coupon.updated",
        entity_type="coupon_code",
        entity_id=coupon.id,
        metadata=metadata,
    )
    await session.commit()
    return coupon
