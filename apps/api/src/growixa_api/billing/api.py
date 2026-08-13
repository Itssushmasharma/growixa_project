from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.billing.providers.razorpay_provider import RazorpayProvider
from growixa_api.billing.schemas import RazorpayWebhookPayload
from growixa_api.billing.services import process_razorpay_webhook
from growixa_api.config import get_settings
from growixa_api.db import get_session

public_router = APIRouter(tags=["billing-public"])


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
