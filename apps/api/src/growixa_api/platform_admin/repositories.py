import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Row, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.billing.models import AccountSubscription, SubscriptionPlan
from growixa_api.campaigns.models import Campaign
from growixa_api.platform_admin.models import SupportSession
from growixa_api.usage.models import UsageRecord
from growixa_api.users.models import User


async def list_accounts(session: AsyncSession) -> Sequence[Account]:
    result = await session.execute(select(Account).order_by(Account.created_at))
    return result.scalars().all()


async def get_account_by_id(session: AsyncSession, account_id: uuid.UUID) -> Account | None:
    return await session.get(Account, account_id)


async def count_users_by_account(session: AsyncSession) -> dict[uuid.UUID, int]:
    stmt = select(User.account_id, func.count(User.id)).group_by(User.account_id)
    result = await session.execute(stmt)
    return {account_id: count for account_id, count in result.all()}


async def list_usage_summary(
    session: AsyncSession,
) -> Sequence[Row[tuple[uuid.UUID, str, str, float, str]]]:
    """One row per (account, operation_type) with quantity summed -- GRX-SAAS-008 /
    DEC-GRX-021 point 3: an aggregate, never a raw per-record cross-account dump."""
    stmt = (
        select(
            UsageRecord.account_id,
            Account.name,
            UsageRecord.operation_type,
            func.sum(UsageRecord.quantity).label("total_quantity"),
            UsageRecord.unit,
        )
        .join(Account, Account.id == UsageRecord.account_id)
        .group_by(
            UsageRecord.account_id, Account.name, UsageRecord.operation_type, UsageRecord.unit
        )
        .order_by(Account.name, UsageRecord.operation_type)
    )
    result = await session.execute(stmt)
    return result.all()


async def list_campaigns_by_status(
    session: AsyncSession, *, statuses: Sequence[str]
) -> Sequence[Row[tuple[Campaign, str]]]:
    """Cross-account by design (GRX-SAAS-008) -- never account_id-scoped. Returns only
    scheduling metadata via the Campaign row itself; callers must not surface
    subject/body_html/body_text (THREAT_MODEL.md T37)."""
    stmt = (
        select(Campaign, Account.name)
        .join(Account, Account.id == Campaign.account_id)
        .where(Campaign.status.in_(statuses))
        .order_by(Campaign.updated_at.desc())
    )
    result = await session.execute(stmt)
    return result.all()


async def get_campaign_by_id(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    return await session.get(Campaign, campaign_id)


async def create_support_session(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    platform_admin_id: uuid.UUID,
    reason: str,
    ticket_number: str,
    access_level: str,
    expires_at: datetime,
) -> SupportSession:
    support_session = SupportSession(
        account_id=account_id,
        platform_admin_id=platform_admin_id,
        reason=reason,
        ticket_number=ticket_number,
        access_level=access_level,
        expires_at=expires_at,
    )
    session.add(support_session)
    await session.flush()
    return support_session


async def get_support_session_by_id(
    session: AsyncSession, support_session_id: uuid.UUID
) -> SupportSession | None:
    return await session.get(SupportSession, support_session_id)


async def list_support_sessions_for_account(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SupportSession]:
    result = await session.execute(
        select(SupportSession)
        .where(SupportSession.account_id == account_id)
        .order_by(SupportSession.started_at.desc())
    )
    return result.scalars().all()


async def get_active_support_session_for_account(
    session: AsyncSession, account_id: uuid.UUID
) -> SupportSession | None:
    """The one query the customer-facing banner check (THREAT_MODEL.md T42) needs --
    served by the partial (account_id) WHERE ended_at IS NULL index."""
    result = await session.execute(
        select(SupportSession)
        .where(
            SupportSession.account_id == account_id,
            SupportSession.ended_at.is_(None),
            SupportSession.expires_at > func.now(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def count_active_accounts(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Account.id)).where(Account.status == "ACTIVE"))
    return result.scalar_one()


async def get_mrr_totals(session: AsyncSession) -> tuple[float, float]:
    """Sums each ACTIVE subscription's plan price, filtered to that subscription's own
    billing currency -- a `SubscriptionPlan` row carries both `price_usd` and
    `price_inr` (needed so the plan can be offered in either currency), so summing both
    unconditionally would credit a USD subscriber's price to the INR total too (real
    bug found and fixed in GRX-SAAS-009 review: confirmed live, a lone USD subscriber
    was inflating INR MRR to a nonzero figure with zero real INR subscribers). NULL or
    zero-priced plans (Enterprise / contact-sales, Free) contribute 0 -- there is no
    self-serve price to sum."""
    result = await session.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (AccountSubscription.currency == "USD", SubscriptionPlan.price_usd),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (AccountSubscription.currency == "INR", SubscriptionPlan.price_inr),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .select_from(AccountSubscription)
        .join(SubscriptionPlan, SubscriptionPlan.id == AccountSubscription.plan_id)
        .where(AccountSubscription.status == "ACTIVE")
    )
    row = result.one()
    return float(row[0]), float(row[1])


async def count_active_paying_subscriptions(session: AsyncSession) -> int:
    """ACTIVE subscriptions on a plan with a real price in that subscription's own
    currency. Every account gets an ACTIVE Free subscription at registration
    (create_default_free_subscription), so a raw ACTIVE count would be dominated by
    non-paying accounts and misread as paying customers on a financial dashboard
    (real bug found and fixed in GRX-SAAS-009 review: confirmed live, 36 of 37 ACTIVE
    subscriptions were Free -- one real paying customer)."""
    result = await session.execute(
        select(func.count())
        .select_from(AccountSubscription)
        .join(SubscriptionPlan, SubscriptionPlan.id == AccountSubscription.plan_id)
        .where(
            AccountSubscription.status == "ACTIVE",
            case(
                (AccountSubscription.currency == "USD", SubscriptionPlan.price_usd),
                (AccountSubscription.currency == "INR", SubscriptionPlan.price_inr),
                else_=0,
            )
            > 0,
        )
    )
    return result.scalar_one()


async def count_subscriptions_canceled_since(session: AsyncSession, *, since: datetime) -> int:
    """Count of subscriptions with status=CANCELED whose `updated_at` falls on/after
    `since` -- used for churn (GRX-SAAS-009). There is no dedicated
    subscription-status-change history table, so `updated_at` on a CANCELED row is
    used as an approximation of "when this subscription churned". Documented
    approximation, not silently assumed -- see get_financial_metrics's docstring for
    the exact churn-rate definition."""
    result = await session.execute(
        select(func.count())
        .select_from(AccountSubscription)
        .where(AccountSubscription.status == "CANCELED", AccountSubscription.updated_at >= since)
    )
    return result.scalar_one()


async def get_period_usage_totals(session: AsyncSession) -> tuple[int, int]:
    """Sums each account's current-billing-period usage counters directly -- these are
    the same `period_email_used`/`period_ai_used` values the quota evaluator itself
    reads (GRX-BILL-005), so this is the platform-wide total of exactly that, not a
    calendar-month re-derivation from raw send/generation events."""
    result = await session.execute(
        select(
            func.coalesce(func.sum(AccountSubscription.period_email_used), 0),
            func.coalesce(func.sum(AccountSubscription.period_ai_used), 0),
        )
    )
    row = result.one()
    return int(row[0]), int(row[1])


async def get_plan_distribution(session: AsyncSession) -> Sequence[Row[tuple[str, str, int]]]:
    """One row per plan with an active subscriber -- not hardcoded to the original four
    tiers, since GRX-SAAS-006 lets a platform admin create genuinely new plans."""
    result = await session.execute(
        select(
            SubscriptionPlan.slug,
            SubscriptionPlan.name,
            func.count(AccountSubscription.id),
        )
        .join(AccountSubscription, AccountSubscription.plan_id == SubscriptionPlan.id)
        .where(AccountSubscription.status == "ACTIVE")
        .group_by(SubscriptionPlan.slug, SubscriptionPlan.name)
        .order_by(SubscriptionPlan.slug)
    )
    return result.all()
