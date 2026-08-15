import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.models import (
    AccountCreditBalance,
    AccountSubscription,
    CouponCode,
    CreditPack,
    SubscriptionPlan,
)
from growixa_api.billing.providers.base import PaymentGatewayProvider
from growixa_api.billing.repositories import (
    create_coupon,
    create_credit_pack,
    create_plan,
    get_account_subscription,
    get_account_subscription_by_razorpay_subscription_id,
    get_account_subscription_with_plan,
    get_coupon_by_code,
    get_coupon_by_id,
    get_coupon_redemption,
    get_credit_balance,
    get_credit_pack_by_id,
    get_credit_pack_by_slug,
    get_credit_pack_by_slug_any_status,
    get_locked_account_subscription_with_plan,
    get_plan_by_id,
    get_plan_by_slug,
    grant_credits,
    list_active_credit_packs,
    list_all_credit_packs,
    list_coupons,
    list_credit_balances,
    list_plans,
    record_coupon_redemption,
    record_credit_purchase_idempotent,
    set_coupon_active,
    set_pending_subscription,
    update_credit_pack,
    update_plan,
)

logger = logging.getLogger(__name__)


class PlanNotFoundError(Exception):
    pass


class CreditPackNotFoundError(Exception):
    pass


class PlanSlugAlreadyExistsError(Exception):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"a plan with slug {slug!r} already exists")


class CreditPackSlugAlreadyExistsError(Exception):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"a credit pack with slug {slug!r} already exists")


class CurrencyNotAvailableError(Exception):
    """The plan/pack exists, but has no Razorpay Plan (or price) for the requested
    currency yet -- e.g. USD before international payments are approved on the
    Razorpay account (a real limitation hit live while building this task, not a
    hypothetical)."""


class CouponNotFoundError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"coupon {code!r} not found")


class CouponInactiveError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"coupon {code!r} is not active")


class CouponExpiredError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"coupon {code!r} has expired")


class CouponRedemptionLimitReachedError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"coupon {code!r} has reached its redemption limit")


class CouponNotEligibleForPlanError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"coupon {code!r} is not eligible for this plan")


class CouponAlreadyRedeemedError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"coupon {code!r} has already been redeemed by this account")


class CouponWrongTypeForActionError(Exception):
    """The coupon exists and is otherwise valid, but its discount_type doesn't fit
    where it's being applied -- e.g. a CREDIT_GRANT code passed to a top-up checkout,
    or a PERCENTAGE/FIXED_AMOUNT code passed to /billing/redeem-coupon."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CouponMissingCreditTypeError(Exception):
    """A CREDIT_GRANT coupon is being created without credit_type set -- there'd be
    nothing to credit on redemption."""


class CouponCodeAlreadyExistsError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"a coupon with code {code!r} already exists")


class QuotaExceededError(Exception):
    """Neither the plan's monthly allowance nor the account's credit balance covers a
    period-metered operation (email send / AI run). Callers map this to HTTP 402."""

    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(f"quota exceeded for {operation!r}")


class PlanLimitExceededError(Exception):
    """The account is already at its plan's cap for an inventory-style resource
    (contacts / social accounts / user seats). Callers map this to HTTP 402."""

    def __init__(self, resource: str) -> None:
        self.resource = resource
        super().__init__(f"plan limit reached for {resource!r}")


@dataclass(frozen=True)
class _MeteredOperation:
    period_used_attr: str
    plan_limit_attr: str
    credit_type: str


# email/ai_run's three names (the AccountSubscription counter column, the
# SubscriptionPlan limit column, and the account_credit_balances.credit_type value)
# don't share a single naming convention with each other -- deliberately explicit here
# rather than derived via string formatting, which BILLING_SYSTEM_ARCHITECTURE.md §4's
# original pseudocode did and got wrong (e.g. "ai_run".upper() == "AI_RUN", not the
# real credit_type "AI_RUNS").
_METERED_OPERATIONS: dict[str, _MeteredOperation] = {
    "email": _MeteredOperation("period_email_used", "max_monthly_emails", "EMAIL_SENDS"),
    "ai_run": _MeteredOperation("period_ai_used", "max_monthly_ai_runs", "AI_RUNS"),
}

# Statuses under which an account keeps its plan_id's real limits. PENDING (checkout
# not yet confirmed -- plan_id already points at the *target* plan per
# set_pending_subscription, so it must not be trusted yet) and HALTED (billing broken)
# both fall back to the Free plan's allowance instead. CANCELED stays here deliberately:
# the webhook handler below leaves current_period_end untouched on cancellation so the
# account keeps its plan's features until the period genuinely ends -- GRX-BILL-006's
# ticker is what actually downgrades plan_id, not this evaluator.
_STATUSES_HONORING_PLAN_LIMITS = frozenset({"ACTIVE", "PAST_DUE", "CANCELED"})


async def _resolve_effective_limit(
    session: AsyncSession,
    subscription: AccountSubscription,
    plan: SubscriptionPlan,
    limit_attr: str,
) -> int | None:
    if subscription.status in _STATUSES_HONORING_PLAN_LIMITS:
        return getattr(plan, limit_attr)  # type: ignore[no-any-return]
    free_plan = await get_plan_by_slug(session, "free")
    assert free_plan is not None, "the free plan is always seeded"
    return getattr(free_plan, limit_attr)  # type: ignore[no-any-return]


async def check_and_consume_quota(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    operation: Literal["email", "ai_run"],
    qty: int = 1,
) -> None:
    """Atomic quota evaluator (`BILLING_SYSTEM_ARCHITECTURE.md` §4): consumes `qty`
    units of a period-metered operation against the account's monthly plan allowance,
    falling back to its non-expiring credit balance for any overage. Locks the
    subscription row for the duration and commits its own transaction on every path --
    callers must call this before any other uncommitted work they want to survive a
    QuotaExceededError, matching how `ai/services.py`'s `generate()` calls this before
    spending any real provider budget."""
    spec = _METERED_OPERATIONS[operation]
    subscription, plan = await get_locked_account_subscription_with_plan(session, account_id)
    limit = await _resolve_effective_limit(session, subscription, plan, spec.plan_limit_attr)
    current_used: int = getattr(subscription, spec.period_used_attr)

    if limit is None:  # NULL = unlimited (Enterprise, or an admin override)
        setattr(subscription, spec.period_used_attr, current_used + qty)
        await session.commit()
        return

    if current_used + qty <= limit:
        setattr(subscription, spec.period_used_attr, current_used + qty)
        await session.commit()
        return

    # Plan allowance partially or fully exhausted -- cover only the exact overage from
    # credits, not the full qty.
    already_covered = max(0, limit - current_used)
    needed_extra = qty - already_covered

    credit_result = await session.execute(
        text(
            """
            UPDATE account_credit_balances
            SET remaining_credits = remaining_credits - :needed, updated_at = NOW()
            WHERE account_id = :account_id
              AND credit_type = :credit_type
              AND remaining_credits >= :needed
            RETURNING remaining_credits
            """
        ),
        {"needed": needed_extra, "account_id": account_id, "credit_type": spec.credit_type},
    )
    if credit_result.first() is not None:
        setattr(subscription, spec.period_used_attr, limit)  # monthly side maxed out
        await session.commit()
        return

    await session.rollback()  # release the row lock; nothing here was actually changed
    raise QuotaExceededError(operation)


async def check_plan_limit(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    limit_attr: str,
    current_count: int,
    resource: str,
) -> None:
    """Point-in-time cap check (current count vs. plan limit, no period reset) for
    inventory-style resources -- contacts / social accounts / user seats. Unlike
    `check_and_consume_quota`, there's no counter to decrement and no credit fallback,
    so this is a plain read (no row lock): the caller supplies its own
    already-computed current count from its own table (a lock on `account_subscriptions`
    wouldn't serialize a `COUNT(*)` against an unrelated table anyway). Best-effort, not
    strictly serializable -- two simultaneous creates for the same account right at the
    boundary could both pass, the same tolerance most soft plan-limit enforcement
    accepts."""
    subscription = await get_account_subscription(session, account_id)
    assert subscription is not None, "every account has exactly one row (GRX-BILL-002)"
    plan = await session.get(SubscriptionPlan, subscription.plan_id)
    assert plan is not None, "account_subscriptions.plan_id always references a real plan"

    limit = await _resolve_effective_limit(session, subscription, plan, limit_attr)
    if limit is not None and current_count >= limit:
        raise PlanLimitExceededError(resource)


# Event types this handler actively acts on -- Razorpay sends many other event types
# (refund.*, order.paid, subscription.pending, subscription.completed, etc.) that this
# slice doesn't need; anything not listed here is a deliberate, silent no-op rather
# than an error, since an unhandled-but-legitimate event isn't a failure.
_SUBSCRIPTION_SYNCED_EVENTS = {"subscription.activated", "subscription.charged"}


async def process_razorpay_webhook(
    session: AsyncSession, *, event: str, payload: dict[str, Any]
) -> None:
    """Dispatches a signature-already-verified Razorpay webhook event to the right
    handler. Never raises on an unrecognized event, an unknown razorpay_subscription_id,
    or a malformed-but-irrelevant payload shape -- a webhook endpoint's job is to
    acknowledge receipt (HTTP 2xx) so Razorpay doesn't retry indefinitely, not to
    validate Razorpay's own event catalog."""
    if event in _SUBSCRIPTION_SYNCED_EVENTS:
        await _handle_subscription_synced(session, payload)
    elif event == "subscription.halted":
        await _handle_subscription_status_change(session, payload, status="HALTED")
    elif event == "subscription.cancelled":
        # Status only -- current_period_end is untouched, so the account keeps its
        # plan's features until the period genuinely ends. The actual downgrade to
        # Free happens later, via the cancellation-downgrade ticker (GRX-BILL-006),
        # not here.
        await _handle_subscription_status_change(session, payload, status="CANCELED")
    elif event == "payment.captured":
        await _handle_payment_captured(session, payload)
    else:
        logger.info("razorpay webhook: ignoring unhandled event type %r", event)


def _subscription_entity(payload: dict[str, Any]) -> dict[str, Any] | None:
    entity: dict[str, Any] | None = payload.get("subscription", {}).get("entity")
    return entity


async def _handle_subscription_synced(session: AsyncSession, payload: dict[str, Any]) -> None:
    entity = _subscription_entity(payload)
    if entity is None or "id" not in entity:
        logger.warning("razorpay webhook: subscription event missing payload.subscription.entity")
        return

    subscription = await get_account_subscription_by_razorpay_subscription_id(session, entity["id"])
    if subscription is None:
        logger.warning(
            "razorpay webhook: no account_subscriptions row for razorpay_subscription_id=%r",
            entity["id"],
        )
        return

    subscription.status = "ACTIVE"
    current_end = entity.get("current_end")
    if current_end is not None:
        subscription.current_period_end = datetime.fromtimestamp(int(current_end), tz=UTC)
    subscription.period_email_used = 0
    subscription.period_ai_used = 0
    await session.commit()


async def _handle_subscription_status_change(
    session: AsyncSession, payload: dict[str, Any], *, status: str
) -> None:
    entity = _subscription_entity(payload)
    if entity is None or "id" not in entity:
        logger.warning("razorpay webhook: subscription event missing payload.subscription.entity")
        return

    subscription = await get_account_subscription_by_razorpay_subscription_id(session, entity["id"])
    if subscription is None:
        logger.warning(
            "razorpay webhook: no account_subscriptions row for razorpay_subscription_id=%r",
            entity["id"],
        )
        return

    subscription.status = status
    await session.commit()


async def _handle_payment_captured(session: AsyncSession, payload: dict[str, Any]) -> None:
    """`payment.captured` fires both for subscription-cycle charges (already handled
    via `subscription.charged` above) and for one-time top-up Order payments. Only the
    latter is acted on here, distinguished by an explicit `notes.kind == "credit_topup"`
    marker that GRX-BILL-004's checkout flow sets when creating the Order -- inferring
    this from Razorpay's payload shape instead would be fragile."""
    entity: dict[str, Any] | None = payload.get("payment", {}).get("entity")
    if entity is None:
        return

    notes = entity.get("notes") or {}
    if notes.get("kind") != "credit_topup":
        return  # a subscription-cycle payment, or something else entirely -- not ours to act on

    try:
        account_id = uuid.UUID(notes["account_id"])
        credit_type = notes["credit_type"]
        credits_added = int(notes["credits"])
    except (KeyError, TypeError, ValueError):
        logger.warning(
            "razorpay webhook: payment.captured has kind=credit_topup but malformed notes: %r",
            notes,
        )
        return

    credited = await record_credit_purchase_idempotent(
        session,
        account_id=account_id,
        credit_type=credit_type,
        credits_added=credits_added,
        razorpay_payment_id=entity["id"],
    )
    if credited:
        await session.commit()
    else:
        logger.info(
            "razorpay webhook: payment %r already processed, skipping duplicate credit",
            entity["id"],
        )


async def create_subscription_checkout(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    plan_slug: str,
    currency: Literal["USD", "INR"],
    gateway: PaymentGatewayProvider,
) -> str:
    """Creates the Razorpay Subscription and immediately stores its id on the
    account's row as `PENDING` (BILLING_SYSTEM_ARCHITECTURE.md §6, GRX-BILL-004) --
    the row must be findable by `razorpay_subscription_id` the moment the
    `subscription.activated`/`charged` webhook fires, which can happen seconds after
    the customer completes Razorpay's Checkout widget. Returns the subscription id the
    frontend hands to that widget; nothing is granted until the webhook confirms."""
    plan = await get_plan_by_slug(session, plan_slug)
    if plan is None:
        raise PlanNotFoundError(plan_slug)

    gateway_plan_id = plan.razorpay_plan_id_usd if currency == "USD" else plan.razorpay_plan_id_inr
    if gateway_plan_id is None:
        raise CurrencyNotAvailableError(f"{plan_slug} is not available in {currency} yet")

    gateway_subscription = await gateway.create_subscription(
        gateway_plan_id=gateway_plan_id,
        notes={"account_id": str(account_id), "plan_slug": plan_slug},
    )
    await set_pending_subscription(
        session,
        account_id=account_id,
        plan_id=plan.id,
        currency=currency,
        razorpay_subscription_id=gateway_subscription.gateway_subscription_id,
    )
    return gateway_subscription.gateway_subscription_id


async def _validate_coupon_for_redemption(
    session: AsyncSession, *, code: str, account_id: uuid.UUID, plan_slug: str | None
) -> CouponCode:
    """Every constraint from `BILLING_SYSTEM_ARCHITECTURE.md` §7.3 in one place:
    `is_active`, not expired, under `max_redemptions`, plan-eligible (if restricted),
    and not already redeemed by this account (`THREAT_MODEL.md` T65's one-redemption-
    per-account rule -- the real enforcement is `coupon_redemptions`' unique
    constraint; this is the pre-check that gives a clean error instead of a raw
    `IntegrityError`)."""
    coupon = await get_coupon_by_code(session, code)
    if coupon is None:
        raise CouponNotFoundError(code)
    if not coupon.is_active:
        raise CouponInactiveError(code)
    if coupon.expires_at is not None and coupon.expires_at <= datetime.now(UTC):
        raise CouponExpiredError(code)
    if coupon.max_redemptions is not None and coupon.redemption_count >= coupon.max_redemptions:
        raise CouponRedemptionLimitReachedError(code)
    if (
        coupon.applicable_plan_slugs is not None
        and plan_slug is not None
        and plan_slug not in coupon.applicable_plan_slugs
    ):
        raise CouponNotEligibleForPlanError(code)
    if await get_coupon_redemption(session, coupon.id, account_id) is not None:
        raise CouponAlreadyRedeemedError(code)
    return coupon


def _apply_coupon_discount(amount_smallest_unit: int, coupon: CouponCode) -> int:
    if coupon.discount_type == "PERCENTAGE":
        discounted = amount_smallest_unit * (1 - float(coupon.discount_value) / 100)
    else:  # FIXED_AMOUNT -- discount_value is in the major currency unit (e.g. dollars/rupees)
        discounted = amount_smallest_unit - int(coupon.discount_value) * 100
    # Razorpay rejects near-zero amounts outright -- a coupon can discount a top-up
    # deeply, but never to "free" (that's what a CREDIT_GRANT coupon is for).
    return max(100, round(discounted))


async def redeem_credit_grant_coupon(
    session: AsyncSession, *, account_id: uuid.UUID, code: str
) -> AccountCreditBalance:
    """`POST /billing/redeem-coupon` -- the dedicated path for `CREDIT_GRANT` coupons
    (`BILLING_SYSTEM_ARCHITECTURE.md` §7.3: "credit-grant coupons never touch Razorpay
    at all"). `PERCENTAGE`/`FIXED_AMOUNT` codes are rejected here -- they're applied at
    checkout instead (`create_topup_checkout` below)."""
    current_subscription = await get_account_subscription_with_plan(session, account_id)
    current_plan_slug = current_subscription[1].slug if current_subscription is not None else None
    coupon = await _validate_coupon_for_redemption(
        session, code=code, account_id=account_id, plan_slug=current_plan_slug
    )
    if coupon.discount_type != "CREDIT_GRANT":
        raise CouponWrongTypeForActionError(
            f"{code} is a {coupon.discount_type} coupon -- apply it at checkout instead"
        )
    assert coupon.credit_type is not None, "CREDIT_GRANT coupons always have credit_type set"

    await grant_credits(
        session,
        account_id=account_id,
        credit_type=coupon.credit_type,
        credits=int(coupon.discount_value),
        granted_by_platform_admin_id=None,
    )
    await record_coupon_redemption(session, coupon=coupon, account_id=account_id)
    await session.commit()

    balance = await get_credit_balance(session, account_id, coupon.credit_type)
    assert balance is not None, "grant_credits always leaves a row for this (account, credit_type)"
    return balance


async def create_topup_checkout(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    pack_slug: str,
    currency: Literal["USD", "INR"],
    coupon_code: str | None,
    gateway: PaymentGatewayProvider,
) -> tuple[str, int]:
    """Creates a one-time Razorpay Order for a top-up credit pack -- unlike
    subscribing, nothing about the pack purchase itself is written to any table here;
    the account is only ever credited by the `payment.captured` webhook handler above,
    keyed off the `notes.kind=credit_topup` marker set here. Returns
    (razorpay_order_id, amount_smallest_unit) for the frontend's checkout widget.

    A `PERCENTAGE`/`FIXED_AMOUNT` coupon, if given, discounts `amount_smallest_unit`
    directly -- Razorpay Orders take an arbitrary amount, so this needs no Razorpay-side
    "offer" mechanism (unlike a Subscription, whose recurring amount is fixed by its
    immutable Plan object; `GRX-BILL-004`/§4a, `POST /billing/subscribe` does not
    accept a coupon for this reason -- verified against Razorpay's own Checkout.js
    parameter reference, which documents no offer/discount parameter for subscription
    checkout). The redemption is recorded only *after* the real Razorpay Order call
    succeeds, so a failed gateway call never consumes the coupon -- but *before* the
    customer completes Razorpay's Checkout widget, so an abandoned checkout does
    consume it (a deliberate, accepted tradeoff: recording it later, only once
    `payment.captured` fires, would let the same account create multiple discounted
    Orders in parallel before paying for any of them)."""
    pack = await get_credit_pack_by_slug(session, pack_slug)
    if pack is None:
        raise CreditPackNotFoundError(pack_slug)

    price = pack.price_usd if currency == "USD" else pack.price_inr
    if price is None:
        raise CurrencyNotAvailableError(f"{pack_slug} is not available in {currency} yet")

    amount_smallest_unit = int(price * 100)

    coupon: CouponCode | None = None
    if coupon_code is not None:
        current_subscription = await get_account_subscription_with_plan(session, account_id)
        current_plan_slug = (
            current_subscription[1].slug if current_subscription is not None else None
        )
        coupon = await _validate_coupon_for_redemption(
            session, code=coupon_code, account_id=account_id, plan_slug=current_plan_slug
        )
        if coupon.discount_type not in ("PERCENTAGE", "FIXED_AMOUNT"):
            raise CouponWrongTypeForActionError(
                f"{coupon_code} can't be applied to a top-up purchase -- "
                "redeem it via /billing/redeem-coupon instead"
            )
        amount_smallest_unit = _apply_coupon_discount(amount_smallest_unit, coupon)

    gateway_order = await gateway.create_order(
        amount_smallest_unit=amount_smallest_unit,
        currency=currency,
        notes={
            "kind": "credit_topup",
            "account_id": str(account_id),
            "credit_type": pack.credit_type,
            "credits": str(pack.credits),
        },
    )
    if coupon is not None:
        await record_coupon_redemption(session, coupon=coupon, account_id=account_id)
        await session.commit()
    return gateway_order.gateway_order_id, amount_smallest_unit


async def get_billing_overview(
    session: AsyncSession, account_id: uuid.UUID
) -> tuple[AccountSubscription, SubscriptionPlan, Sequence[AccountCreditBalance]]:
    """Read model for the customer billing page (`GRX-BILL-007`): the account's current
    plan, subscription state, and every credit balance it has (a credit type with no
    purchase/grant yet simply has no row -- the frontend defaults it to 0)."""
    result = await get_account_subscription_with_plan(session, account_id)
    assert result is not None, "every account has exactly one row (GRX-BILL-002)"
    subscription, plan = result
    balances = await list_credit_balances(session, account_id)
    return subscription, plan, balances


async def list_plan_catalog(session: AsyncSession) -> Sequence[SubscriptionPlan]:
    return await list_plans(session)


async def list_credit_pack_catalog(session: AsyncSession) -> Sequence[CreditPack]:
    return await list_active_credit_packs(session)


async def list_credit_pack_catalog_for_admin(session: AsyncSession) -> Sequence[CreditPack]:
    """Unlike list_credit_pack_catalog (customer-facing), includes deactivated packs
    too -- a platform admin managing the catalog (GRX-SAAS-006) needs to see and
    reactivate them, not just the currently-purchasable set."""
    return await list_all_credit_packs(session)


class NoOverrideFieldsProvidedError(Exception):
    """The platform-admin subscription-override request supplied neither plan_slug nor
    status -- there's nothing to change."""


async def admin_override_subscription(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    plan_slug: str | None,
    status: str | None,
    platform_admin_id: uuid.UUID,
) -> tuple[AccountSubscription, SubscriptionPlan]:
    """Platform-admin manual plan/status override (`GRX-SAAS-006`,
    `BILLING_SYSTEM_ARCHITECTURE.md` §6.1/§6.3 -- merged into one call here since the
    original draft's two separate routes collided with the pre-existing
    `PATCH /platform/accounts/{id}/status` account-status route). Bypasses Razorpay
    entirely -- no payment, no webhook. Deliberately does NOT commit -- the caller
    (`platform_admin/services.py`) writes an audit-log entry for this action and commits
    both together in one transaction, matching every other platform-admin mutation's
    "state change + audit event, one commit" shape; it's also responsible for
    confirming the account itself exists before calling this, so the assert below only
    guards the `GRX-BILL-002` "every account has exactly one subscription row"
    invariant, not a bad `account_id`."""
    if plan_slug is None and status is None:
        raise NoOverrideFieldsProvidedError

    subscription = await get_account_subscription(session, account_id)
    assert subscription is not None, "every account has exactly one row (GRX-BILL-002)"

    if plan_slug is not None:
        plan = await get_plan_by_slug(session, plan_slug)
        if plan is None:
            raise PlanNotFoundError(plan_slug)
        subscription.plan_id = plan.id
    if status is not None:
        subscription.status = status
    subscription.set_by_platform_admin_id = platform_admin_id
    await session.flush()

    result = await get_account_subscription_with_plan(session, account_id)
    assert result is not None
    return result


async def admin_grant_credits(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    credit_type: str,
    credits: int,
    platform_admin_id: uuid.UUID,
) -> AccountCreditBalance:
    """Platform-admin free credit grant (`GRX-SAAS-006` §6.2) -- e.g. support/VIP
    comps. Same underlying table writes as a real top-up purchase
    (`account_credit_balances`/`account_credit_purchases`), distinguishable in the
    receipt history by `razorpay_payment_id IS NULL` and `granted_by_platform_admin_id`
    being set instead. No internal commit -- see `admin_override_subscription`'s
    docstring for why."""
    await grant_credits(
        session,
        account_id=account_id,
        credit_type=credit_type,
        credits=credits,
        granted_by_platform_admin_id=platform_admin_id,
    )
    await session.flush()
    balance = await get_credit_balance(session, account_id, credit_type)
    assert balance is not None, "grant_credits always leaves a row for this (account, credit_type)"
    return balance


async def admin_create_plan(session: AsyncSession, *, fields: dict[str, Any]) -> SubscriptionPlan:
    """`GRX-SAAS-006` §6.4 -- a genuine *create*, not just edit, per the product
    owner's explicit request. `subscription_plans.slug`'s CHECK was widened
    (`e3e939e991f4`) from a fixed 4-value whitelist to a plain format check
    specifically so this isn't limited to editing the four seeded tiers. No internal
    commit -- see `admin_override_subscription`'s docstring for why."""
    existing = await get_plan_by_slug(session, fields["slug"])
    if existing is not None:
        raise PlanSlugAlreadyExistsError(fields["slug"])
    return await create_plan(session, fields)


async def admin_update_plan(
    session: AsyncSession, *, plan_id: uuid.UUID, fields: dict[str, Any]
) -> SubscriptionPlan:
    """Edits a plan's quotas/prices/features platform-wide -- affects every account on
    that plan going forward, does not retroactively touch `account_subscriptions` rows
    already mid-period (§6.4). No internal commit."""
    plan = await get_plan_by_id(session, plan_id)
    if plan is None:
        raise PlanNotFoundError(str(plan_id))
    return await update_plan(session, plan, fields)


async def admin_create_credit_pack(session: AsyncSession, *, fields: dict[str, Any]) -> CreditPack:
    """No internal commit -- see `admin_override_subscription`'s docstring for why."""
    existing = await get_credit_pack_by_slug_any_status(session, fields["slug"])
    if existing is not None:
        raise CreditPackSlugAlreadyExistsError(fields["slug"])
    return await create_credit_pack(session, fields)


async def admin_update_credit_pack(
    session: AsyncSession, *, pack_id: uuid.UUID, fields: dict[str, Any]
) -> CreditPack:
    """No internal commit -- see `admin_override_subscription`'s docstring for why."""
    pack = await get_credit_pack_by_id(session, pack_id)
    if pack is None:
        raise CreditPackNotFoundError(str(pack_id))
    return await update_credit_pack(session, pack, fields)


async def list_coupon_catalog(session: AsyncSession) -> Sequence[CouponCode]:
    return await list_coupons(session)


async def admin_create_coupon(
    session: AsyncSession, *, created_by_platform_admin_id: uuid.UUID, fields: dict[str, Any]
) -> CouponCode:
    """`GRX-SAAS-012` §7.2. No internal commit -- see `admin_override_subscription`'s
    docstring for why."""
    if fields["discount_type"] == "CREDIT_GRANT" and fields.get("credit_type") is None:
        raise CouponMissingCreditTypeError
    existing = await get_coupon_by_code(session, fields["code"])
    if existing is not None:
        raise CouponCodeAlreadyExistsError(fields["code"])
    return await create_coupon(
        session, {**fields, "created_by_platform_admin_id": created_by_platform_admin_id}
    )


async def admin_set_coupon_active(
    session: AsyncSession, *, coupon_id: uuid.UUID, is_active: bool
) -> CouponCode:
    """No internal commit -- see `admin_override_subscription`'s docstring for why."""
    coupon = await get_coupon_by_id(session, coupon_id)
    if coupon is None:
        raise CouponNotFoundError(str(coupon_id))
    return await set_coupon_active(session, coupon, is_active)
