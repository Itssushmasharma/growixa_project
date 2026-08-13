import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.repositories import FREE_PLAN_PERIOD_DAYS, get_plan_by_slug
from growixa_api.db import async_session_factory

logger = logging.getLogger("growixa_api")


async def downgrade_expired_cancellations(session: AsyncSession) -> int:
    """Moves every CANCELED subscription whose current_period_end has passed onto a
    fresh Free-tier period. The webhook (GRX-BILL-003) only ever sets
    status = 'CANCELED' and leaves current_period_end untouched, so the account keeps
    its paid plan's features until the period genuinely ends -- nothing else fires
    again at that moment, so this ticker is what actually performs the downgrade
    (BILLING_SYSTEM_ARCHITECTURE.md §5).

    Also resets period_email_used/period_ai_used and gives a fresh
    FREE_PLAN_PERIOD_DAYS-day period -- a downgraded account has no real Razorpay
    object left to ever send another subscription.charged webhook, so nothing else
    would ever reset its monthly counters or roll its period window forward again.
    razorpay_subscription_id and set_by_platform_admin_id are cleared: the former so a
    delayed/replayed webhook for the now-dead subscription can never resurrect it
    (razorpay_customer_id is kept -- that's the person's durable Razorpay identity,
    reusable if they resubscribe later), the latter because it no longer reflects who
    set the *current* plan once the ticker is what changed it.

    Raw SQL, not the ORM, since this updates every matching row in one statement rather
    than loading each AccountSubscription individually -- same shape as
    record_credit_purchase_idempotent's balance UPDATE, including explicitly setting
    updated_at (the ORM's onupdate=func.now() only fires for ORM-driven writes, not raw
    SQL)."""
    free_plan = await get_plan_by_slug(session, "free")
    assert free_plan is not None, "the free plan is always seeded"

    now = datetime.now(UTC)
    result = await session.execute(
        text(
            """
            UPDATE account_subscriptions
            SET plan_id = :free_plan_id,
                status = 'ACTIVE',
                current_period_start = :period_start,
                current_period_end = :period_end,
                period_email_used = 0,
                period_ai_used = 0,
                razorpay_subscription_id = NULL,
                set_by_platform_admin_id = NULL,
                updated_at = :now
            WHERE status = 'CANCELED' AND current_period_end <= :now
            RETURNING account_id
            """
        ),
        {
            "free_plan_id": free_plan.id,
            "period_start": now,
            "period_end": now + timedelta(days=FREE_PLAN_PERIOD_DAYS),
            "now": now,
        },
    )
    downgraded_count = len(result.fetchall())
    await session.commit()
    return downgraded_count


async def run_downgrade_loop(interval_seconds: float) -> None:
    """Runs forever inside the API process (started from app.py's lifespan), alongside
    the campaigns/social schedulers (GRX-SCHED-002, GRX-SOCIAL-007). One bad tick (a
    transient DB blip) is logged and skipped rather than crashing the whole API
    process."""
    logger.info("billing cancellation-downgrade ticker starting (interval=%ss)", interval_seconds)
    while True:
        try:
            async with async_session_factory() as session:
                downgraded = await downgrade_expired_cancellations(session)
                if downgraded:
                    logger.info(
                        "billing downgrade ticker: downgraded %s account(s) to Free", downgraded
                    )
        except Exception:
            logger.exception("billing downgrade ticker tick failed")
        await asyncio.sleep(interval_seconds)
