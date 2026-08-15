import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.models import (
    AccountCreditBalance,
    AccountCreditPurchase,
    AccountSubscription,
    CouponCode,
    CouponRedemption,
    CreditPack,
    SubscriptionPlan,
)

# Not private -- also used by billing/scheduler.py's cancellation-downgrade ticker
# (GRX-BILL-006) to give a downgraded account the same fresh period length a
# brand-new Free signup gets.
FREE_PLAN_PERIOD_DAYS = 30


async def get_plan_by_slug(session: AsyncSession, slug: str) -> SubscriptionPlan | None:
    result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == slug))
    return result.scalar_one_or_none()


async def get_credit_pack_by_slug(session: AsyncSession, slug: str) -> CreditPack | None:
    result = await session.execute(
        select(CreditPack).where(CreditPack.slug == slug, CreditPack.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_account_subscription(
    session: AsyncSession, account_id: uuid.UUID
) -> AccountSubscription | None:
    result = await session.execute(
        select(AccountSubscription).where(AccountSubscription.account_id == account_id)
    )
    return result.scalar_one_or_none()


async def get_account_subscription_with_plan(
    session: AsyncSession, account_id: uuid.UUID
) -> tuple[AccountSubscription, SubscriptionPlan] | None:
    """Unlocked read-only counterpart to get_locked_account_subscription_with_plan
    (GRX-BILL-005) -- for the billing overview GET route (GRX-BILL-007), which has
    nothing to write and shouldn't hold a row lock just to display the page."""
    result = await session.execute(
        select(AccountSubscription, SubscriptionPlan)
        .join(SubscriptionPlan, AccountSubscription.plan_id == SubscriptionPlan.id)
        .where(AccountSubscription.account_id == account_id)
    )
    row = result.first()
    return (row[0], row[1]) if row is not None else None


async def list_plans(session: AsyncSession) -> Sequence[SubscriptionPlan]:
    """The self-serve catalog a billing page picks an upgrade/downgrade from -- every
    plan, in ascending price order (NULLs -- Enterprise's contact-sales tier -- last)."""
    result = await session.execute(
        select(SubscriptionPlan).order_by(SubscriptionPlan.price_usd.nulls_last())
    )
    return result.scalars().all()


async def list_active_credit_packs(session: AsyncSession) -> Sequence[CreditPack]:
    result = await session.execute(
        select(CreditPack)
        .where(CreditPack.is_active.is_(True))
        .order_by(CreditPack.credit_type, CreditPack.credits)
    )
    return result.scalars().all()


async def list_all_credit_packs(session: AsyncSession) -> Sequence[CreditPack]:
    """Every pack regardless of `is_active` -- for the platform-admin catalog view
    (`GRX-SAAS-006`); unlike `list_active_credit_packs` (customer-facing, GRX-BILL-007),
    an admin managing the catalog needs to see (and reactivate) deactivated packs too."""
    result = await session.execute(
        select(CreditPack).order_by(CreditPack.credit_type, CreditPack.credits)
    )
    return result.scalars().all()


async def list_credit_balances(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[AccountCreditBalance]:
    result = await session.execute(
        select(AccountCreditBalance).where(AccountCreditBalance.account_id == account_id)
    )
    return result.scalars().all()


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
        current_period_end=now + timedelta(days=FREE_PLAN_PERIOD_DAYS),
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def get_locked_account_subscription_with_plan(
    session: AsyncSession, account_id: uuid.UUID
) -> tuple[AccountSubscription, SubscriptionPlan]:
    """Locks the account's one subscription row (`SELECT ... FOR UPDATE`) joined to its
    plan -- the atomic quota evaluator (`GRX-BILL-005`) needs both the running counter
    and the limit to decide, and the lock closes the race between two concurrent
    metered requests both reading "under the limit" before either writes back
    (`BILLING_SYSTEM_ARCHITECTURE.md` §4)."""
    result = await session.execute(
        select(AccountSubscription, SubscriptionPlan)
        .join(SubscriptionPlan, AccountSubscription.plan_id == SubscriptionPlan.id)
        .where(AccountSubscription.account_id == account_id)
        .with_for_update(of=AccountSubscription)
    )
    subscription, plan = result.one()
    return subscription, plan


async def get_account_subscription_by_razorpay_subscription_id(
    session: AsyncSession, razorpay_subscription_id: str
) -> AccountSubscription | None:
    result = await session.execute(
        select(AccountSubscription).where(
            AccountSubscription.razorpay_subscription_id == razorpay_subscription_id
        )
    )
    return result.scalar_one_or_none()


async def set_pending_subscription(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    plan_id: uuid.UUID,
    currency: str,
    razorpay_subscription_id: str,
) -> AccountSubscription:
    """Called the moment checkout creates the Razorpay Subscription
    (`POST /billing/subscribe`, GRX-BILL-004) -- stores its id immediately so the
    webhook can find this row by `razorpay_subscription_id` once the customer actually
    authorizes payment. `plan_id` already points at the target plan while `PENDING`;
    nothing is granted until the webhook flips status to `ACTIVE`."""
    subscription = await get_account_subscription(session, account_id)
    assert subscription is not None, "every account has exactly one row (GRX-BILL-002)"

    subscription.plan_id = plan_id
    subscription.currency = currency
    subscription.razorpay_subscription_id = razorpay_subscription_id
    subscription.status = "PENDING"
    await session.commit()
    await session.refresh(subscription)
    return subscription


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


async def grant_credits(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    credit_type: str,
    credits: int,
    granted_by_platform_admin_id: uuid.UUID | None,
) -> None:
    """Free credit grant with no purchase behind it -- either a platform admin
    (`GRX-SAAS-006`, `granted_by_platform_admin_id` set) or a redeemed `CREDIT_GRANT`
    coupon (`GRX-SAAS-012`, left `None` -- the `coupon_redemptions` row recorded
    alongside is the real provenance record for that case, not this column). Same
    two-write shape as `record_credit_purchase_idempotent` above (a receipt row + the
    balance increment), but with no `razorpay_payment_id` to dedupe against: granting
    twice is two real grants, there's no webhook-replay risk to guard against here."""
    session.add(
        AccountCreditPurchase(
            account_id=account_id,
            credit_type=credit_type,
            credits_added=credits,
            razorpay_payment_id=None,
            granted_by_platform_admin_id=granted_by_platform_admin_id,
        )
    )
    balance_stmt = (
        pg_insert(AccountCreditBalance)
        .values(account_id=account_id, credit_type=credit_type, remaining_credits=credits)
        .on_conflict_do_update(
            index_elements=["account_id", "credit_type"],
            set_={
                "remaining_credits": AccountCreditBalance.remaining_credits + credits,
                "updated_at": datetime.now(UTC),
            },
        )
    )
    await session.execute(balance_stmt)


async def get_credit_balance(
    session: AsyncSession, account_id: uuid.UUID, credit_type: str
) -> AccountCreditBalance | None:
    result = await session.execute(
        select(AccountCreditBalance).where(
            AccountCreditBalance.account_id == account_id,
            AccountCreditBalance.credit_type == credit_type,
        )
    )
    return result.scalar_one_or_none()


async def get_plan_by_id(session: AsyncSession, plan_id: uuid.UUID) -> SubscriptionPlan | None:
    result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    return result.scalar_one_or_none()


async def create_plan(session: AsyncSession, fields: dict[str, Any]) -> SubscriptionPlan:
    plan = SubscriptionPlan(**fields)
    session.add(plan)
    await session.flush()
    return plan


async def update_plan(
    session: AsyncSession, plan: SubscriptionPlan, fields: dict[str, Any]
) -> SubscriptionPlan:
    for key, value in fields.items():
        setattr(plan, key, value)
    await session.flush()
    return plan


async def get_credit_pack_by_id(session: AsyncSession, pack_id: uuid.UUID) -> CreditPack | None:
    result = await session.execute(select(CreditPack).where(CreditPack.id == pack_id))
    return result.scalar_one_or_none()


async def get_credit_pack_by_slug_any_status(session: AsyncSession, slug: str) -> CreditPack | None:
    """Unlike `get_credit_pack_by_slug`, doesn't filter to `is_active` -- used for the
    admin create route's slug-uniqueness pre-check (`GRX-SAAS-006`), which must catch a
    collision against a *deactivated* pack too, not just active ones."""
    result = await session.execute(select(CreditPack).where(CreditPack.slug == slug))
    return result.scalar_one_or_none()


async def create_credit_pack(session: AsyncSession, fields: dict[str, Any]) -> CreditPack:
    pack = CreditPack(**fields)
    session.add(pack)
    await session.flush()
    return pack


async def update_credit_pack(
    session: AsyncSession, pack: CreditPack, fields: dict[str, Any]
) -> CreditPack:
    for key, value in fields.items():
        setattr(pack, key, value)
    await session.flush()
    return pack


# --- Coupons (GRX-SAAS-012, BILLING_SYSTEM_ARCHITECTURE.md §7) ---


async def get_coupon_by_code(session: AsyncSession, code: str) -> CouponCode | None:
    result = await session.execute(select(CouponCode).where(CouponCode.code == code))
    return result.scalar_one_or_none()


async def get_coupon_by_id(session: AsyncSession, coupon_id: uuid.UUID) -> CouponCode | None:
    result = await session.execute(select(CouponCode).where(CouponCode.id == coupon_id))
    return result.scalar_one_or_none()


async def list_coupons(session: AsyncSession) -> Sequence[CouponCode]:
    result = await session.execute(select(CouponCode).order_by(CouponCode.created_at.desc()))
    return result.scalars().all()


async def create_coupon(session: AsyncSession, fields: dict[str, Any]) -> CouponCode:
    coupon = CouponCode(**fields)
    session.add(coupon)
    await session.flush()
    return coupon


async def set_coupon_active(
    session: AsyncSession, coupon: CouponCode, is_active: bool
) -> CouponCode:
    coupon.is_active = is_active
    await session.flush()
    return coupon


async def get_coupon_redemption(
    session: AsyncSession, coupon_code_id: uuid.UUID, account_id: uuid.UUID
) -> CouponRedemption | None:
    result = await session.execute(
        select(CouponRedemption).where(
            CouponRedemption.coupon_code_id == coupon_code_id,
            CouponRedemption.account_id == account_id,
        )
    )
    return result.scalar_one_or_none()


async def record_coupon_redemption(
    session: AsyncSession, *, coupon: CouponCode, account_id: uuid.UUID
) -> None:
    """Inserts the `(coupon_code_id, account_id)` redemption row (its unique
    constraint is the real one-redemption-per-account enforcement, `THREAT_MODEL.md`
    T65) and increments `redemption_count` on the same `CouponCode` row the caller
    already loaded -- both writes belong in the same transaction as whatever action
    the redemption is actually for (a credit grant, or a discounted top-up Order),
    so this never commits on its own."""
    session.add(CouponRedemption(coupon_code_id=coupon.id, account_id=account_id))
    coupon.redemption_count += 1
    await session.flush()
