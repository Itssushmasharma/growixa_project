import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.models import AccountSubscription, SubscriptionPlan

_FREE_PLAN_PERIOD_DAYS = 30


async def get_plan_by_slug(session: AsyncSession, slug: str) -> SubscriptionPlan | None:
    result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == slug))
    return result.scalar_one_or_none()


async def get_account_subscription(
    session: AsyncSession, account_id: uuid.UUID
) -> AccountSubscription | None:
    result = await session.execute(
        select(AccountSubscription).where(AccountSubscription.account_id == account_id)
    )
    return result.scalar_one_or_none()


async def create_default_free_subscription(
    session: AsyncSession, account_id: uuid.UUID
) -> AccountSubscription:
    """Every account gets exactly one AccountSubscription row, created here at
    registration (BILLING_SYSTEM_ARCHITECTURE.md §3.4) -- never left absent. Free tier
    has no real Razorpay object, but still gets a real 30-day period so its own
    monthly quota counters (period_email_used/period_ai_used) have something to reset
    against; USD is a plain default since there's no real currency signal at
    registration time -- it's overwritten with the account's chosen currency the
    moment they actually subscribe to a paid plan (GRX-BILL-004)."""
    free_plan = await get_plan_by_slug(session, "free")
    assert free_plan is not None, "the `free` subscription_plans row must be seeded"

    now = datetime.now(UTC)
    subscription = AccountSubscription(
        account_id=account_id,
        plan_id=free_plan.id,
        status="ACTIVE",
        currency="USD",
        current_period_start=now,
        current_period_end=now + timedelta(days=_FREE_PLAN_PERIOD_DAYS),
    )
    session.add(subscription)
    await session.flush()
    return subscription
