import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.repositories import (
    get_account_subscription_by_razorpay_subscription_id,
    record_credit_purchase_idempotent,
)

logger = logging.getLogger(__name__)

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
