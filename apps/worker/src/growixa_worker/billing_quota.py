"""Email-send quota check for send_campaign (GRX-BILL-005).

A duplicated, minimal port of growixa_api.billing.services.check_and_consume_quota's
"email" case -- apps/worker doesn't depend on growixa_api as a library (see models.py's
own docstring), so this can't just be imported. Kept intentionally narrow: only the
single operation the worker ever meters (one email send = one unit), no generic
operation dispatch like the api-side version has room for.
"""

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker.models import AccountSubscription, SubscriptionPlan

# Same status set as growixa_api.billing.services._STATUSES_HONORING_PLAN_LIMITS, for
# the same reason: PENDING/HALTED accounts fall back to the Free plan's allowance
# instead of trusting account_subscriptions.plan_id.
_STATUSES_HONORING_PLAN_LIMITS = frozenset({"ACTIVE", "PAST_DUE", "CANCELED"})


class QuotaExceededError(Exception):
    """Neither the plan's monthly email allowance nor the account's EMAIL_SENDS credit
    balance covers this send."""


async def check_and_consume_email_quota(session: AsyncSession, *, account_id: uuid.UUID) -> None:
    """Locks the account's subscription row, consumes one unit of its monthly email
    allowance (or one EMAIL_SENDS credit on overage), and commits -- own transaction
    boundary, called once per recipient right before the real SMTP send so a blocked
    recipient never reaches send_email."""
    result = await session.execute(
        select(AccountSubscription, SubscriptionPlan)
        .join(SubscriptionPlan, AccountSubscription.plan_id == SubscriptionPlan.id)
        .where(AccountSubscription.account_id == account_id)
        .with_for_update(of=AccountSubscription)
    )
    subscription, plan = result.one()

    if subscription.status in _STATUSES_HONORING_PLAN_LIMITS:
        limit = plan.max_monthly_emails
    else:
        free_plan_result = await session.execute(
            select(SubscriptionPlan.max_monthly_emails).where(SubscriptionPlan.slug == "free")
        )
        limit = free_plan_result.scalar_one()

    if limit is None:  # NULL = unlimited (Enterprise, or an admin override)
        subscription.period_email_used += 1
        await session.commit()
        return

    if subscription.period_email_used + 1 <= limit:
        subscription.period_email_used += 1
        await session.commit()
        return

    credit_result = await session.execute(
        text(
            """
            UPDATE account_credit_balances
            SET remaining_credits = remaining_credits - 1, updated_at = NOW()
            WHERE account_id = :account_id
              AND credit_type = 'EMAIL_SENDS'
              AND remaining_credits >= 1
            RETURNING remaining_credits
            """
        ),
        {"account_id": account_id},
    )
    if credit_result.first() is not None:
        await session.commit()
        return

    await session.rollback()  # release the row lock; nothing here was actually changed
    raise QuotaExceededError(f"email quota exceeded for account {account_id}")
