import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.providers.razorpay_provider import RazorpayProvider
from growixa_api.billing.schemas import (
    RazorpayWebhookPayload,
    SubscribeIn,
    SubscribeOut,
    TopUpIn,
    TopUpOut,
)
from growixa_api.billing.services import (
    CreditPackNotFoundError,
    CurrencyNotAvailableError,
    PlanNotFoundError,
    create_subscription_checkout,
    create_topup_checkout,
    process_razorpay_webhook,
)
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/billing", tags=["billing"])
public_router = APIRouter(tags=["billing-public"])

_require_manage = require_permission("billing.manage")


def _gateway() -> RazorpayProvider:
    settings = get_settings()
    return RazorpayProvider(
        key_id=settings.razorpay_key_id, key_secret=settings.razorpay_key_secret
    )


@router.post("/subscribe", response_model=SubscribeOut, status_code=status.HTTP_201_CREATED)
async def subscribe_route(
    payload: SubscribeIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SubscribeOut:
    try:
        razorpay_subscription_id = await create_subscription_checkout(
            session,
            account_id=account_id,
            plan_slug=payload.plan_slug,
            currency=payload.currency,
            gateway=_gateway(),
        )
    except PlanNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found") from exc
    except CurrencyNotAvailableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return SubscribeOut(
        razorpay_subscription_id=razorpay_subscription_id,
        razorpay_key_id=get_settings().razorpay_key_id,
    )


@router.post("/topup", response_model=TopUpOut, status_code=status.HTTP_201_CREATED)
async def topup_route(
    payload: TopUpIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> TopUpOut:
    try:
        razorpay_order_id, amount_smallest_unit = await create_topup_checkout(
            session,
            account_id=account_id,
            pack_slug=payload.pack_slug,
            currency=payload.currency,
            gateway=_gateway(),
        )
    except CreditPackNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credit pack not found") from exc
    except CurrencyNotAvailableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return TopUpOut(
        razorpay_order_id=razorpay_order_id,
        razorpay_key_id=get_settings().razorpay_key_id,
        amount_smallest_unit=amount_smallest_unit,
        currency=payload.currency,
    )


@public_router.post("/billing/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook_route(
    request: Request,
    x_razorpay_signature: str = Header(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Public per THREAT_MODEL.md's T60 -- authenticated via HMAC signature (Razorpay
    itself is the caller, no user session exists), verified against the raw request
    body before this function ever touches `account_subscriptions`/
    `account_credit_balances`, same "verify before touching any table" shape as the
    existing Postmark webhook (`GRX-EMAIL-005`)."""
    settings = get_settings()
    raw_body = await request.body()

    gateway = RazorpayProvider(
        key_id=settings.razorpay_key_id, key_secret=settings.razorpay_key_secret
    )
    if not gateway.verify_webhook_signature(
        payload=raw_body,
        signature=x_razorpay_signature,
        secret=settings.razorpay_webhook_secret,
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")

    payload = RazorpayWebhookPayload.model_validate_json(raw_body)
    await process_razorpay_webhook(session, event=payload.event, payload=payload.payload)
    return {"status": "ok"}
