import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.providers.base import PaymentGatewayProvider
from growixa_api.billing.repositories import (
    get_account_subscription_by_razorpay_subscription_id,
    get_credit_pack_by_slug,
    get_plan_by_slug,
    record_credit_purchase_idempotent,
    set_pending_subscription,
)

logger = logging.getLogger(__name__)


class PlanNotFoundError(Exception):
    pass


class CreditPackNotFoundError(Exception):
    pass


class CurrencyNotAvailableError(Exception):
    """The plan/pack exists, but has no Razorpay Plan (or price) for the requested
    currency yet -- e.g. USD before international payments are approved on the
    Razorpay account (a real limitation hit live while building this task, not a
    hypothetical)."""


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


async def create_topup_checkout(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    pack_slug: str,
    currency: Literal["USD", "INR"],
    gateway: PaymentGatewayProvider,
) -> tuple[str, int]:
    """Creates a one-time Razorpay Order for a top-up credit pack -- unlike
    subscribing, nothing is written to any table here; the account is only ever
    credited by the `payment.captured` webhook handler above, keyed off the
    `notes.kind=credit_topup` marker set here. Returns (razorpay_order_id,
    amount_smallest_unit) for the frontend's checkout widget."""
    pack = await get_credit_pack_by_slug(session, pack_slug)
    if pack is None:
        raise CreditPackNotFoundError(pack_slug)

    price = pack.price_usd if currency == "USD" else pack.price_inr
    if price is None:
        raise CurrencyNotAvailableError(f"{pack_slug} is not available in {currency} yet")

    amount_smallest_unit = int(price * 100)
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
    return gateway_order.gateway_order_id, amount_smallest_unit
