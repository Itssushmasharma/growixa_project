import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.models import (
    AccountCreditBalance,
    AccountCreditPurchase,
    AccountSubscription,
    SubscriptionPlan,
)

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


async def get_account_subscription_by_razorpay_subscription_id(
    session: AsyncSession, razorpay_subscription_id: str
) -> AccountSubscription | None:
    result = await session.execute(
        select(AccountSubscription).where(
            AccountSubscription.razorpay_subscription_id == razorpay_subscription_id
        )
    )
    return result.scalar_one_or_none()


async def record_credit_purchase_idempotent(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    credit_type: str,
    credits_added: int,
    razorpay_payment_id: str,
) -> bool:
    """Credits `account_credit_balances` for a top-up purchase, but only once per
    `razorpay_payment_id` -- a webhook redelivery of the same `payment.captured` event
    must never double-credit (THREAT_MODEL.md T61). The `account_credit_purchases`
    unique constraint on `razorpay_payment_id` is what makes this atomic: the receipt
    insert is attempted first (`ON CONFLICT DO NOTHING`), and the balance is only
    incremented if that insert actually happened. Returns True if this call was the
    one that credited the account, False if it was a no-op replay."""
    receipt_stmt = (
        pg_insert(AccountCreditPurchase)
        .values(
            account_id=account_id,
            credit_type=credit_type,
            credits_added=credits_added,
            razorpay_payment_id=razorpay_payment_id,
        )
        .on_conflict_do_nothing(index_elements=["razorpay_payment_id"])
        .returning(AccountCreditPurchase.id)
    )
    result = await session.execute(receipt_stmt)
    if result.first() is None:
        return False  # already processed this exact payment

    balance_stmt = (
        pg_insert(AccountCreditBalance)
        .values(account_id=account_id, credit_type=credit_type, remaining_credits=credits_added)
        .on_conflict_do_update(
            index_elements=["account_id", "credit_type"],
            set_={
                "remaining_credits": AccountCreditBalance.remaining_credits + credits_added,
                "updated_at": datetime.now(UTC),
            },
        )
    )
    await session.execute(balance_stmt)
    return True
