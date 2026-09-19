import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.rate_limit import RateLimitExceededError, enforce_rate_limit
from growixa_api.billing.providers.razorpay_provider import RazorpayProvider
from growixa_api.billing.schemas import (
    AccountSubscriptionOut,
    CreditBalanceOut,
    CreditPackOut,
    RazorpayWebhookPayload,
    RedeemCouponIn,
    SubscribeIn,
    SubscribeOut,
    SubscriptionPlanOut,
    TopUpIn,
    TopUpOut,
)
from growixa_api.billing.services import (
    CouponAlreadyRedeemedError,
    CouponExpiredError,
    CouponInactiveError,
    CouponNotEligibleForPlanError,
    CouponNotFoundError,
    CouponRedemptionLimitReachedError,
    CouponWrongTypeForActionError,
    CreditPackNotFoundError,
    CurrencyNotAvailableError,
    PlanNotFoundError,
    create_subscription_checkout,
    create_topup_checkout,
    get_billing_overview,
    list_credit_pack_catalog,
    list_plan_catalog,
    process_razorpay_webhook,
    redeem_credit_grant_coupon,
)
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission
from growixa_api.redis import get_redis

router = APIRouter(prefix="/billing", tags=["billing"])
public_router = APIRouter(tags=["billing-public"])


@public_router.post("/billing/stripe/webhook")
async def stripe_webhook(request: Request) -> None:
    """Razorpay is supported; Stripe ingestion is not yet implemented."""
    raise HTTPException(503, detail="Stripe webhook ingestion is pending integration")


_require_manage = require_permission("billing.manage")
_require_view = require_permission("billing.view")


@router.get("/subscription", response_model=AccountSubscriptionOut)
async def get_subscription_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> AccountSubscriptionOut:
    subscription, plan, balances = await get_billing_overview(session, account_id)
    return AccountSubscriptionOut(
        plan=SubscriptionPlanOut.model_validate(plan),
        status=subscription.status,
        currency=subscription.currency,  # type: ignore[arg-type]
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        period_email_used=subscription.period_email_used,
        period_ai_used=subscription.period_ai_used,
        credit_balances=[CreditBalanceOut.model_validate(b) for b in balances],
    )


@router.get("/plans", response_model=list[SubscriptionPlanOut])
async def list_plans_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[SubscriptionPlanOut]:
    plans = await list_plan_catalog(session)
    return [SubscriptionPlanOut.model_validate(plan) for plan in plans]


@router.get("/credit-packs", response_model=list[CreditPackOut])
async def list_credit_packs_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[CreditPackOut]:
    packs = await list_credit_pack_catalog(session)
    return [CreditPackOut.model_validate(pack) for pack in packs]


def _gateway() -> RazorpayProvider:
    settings = get_settings()
    return RazorpayProvider(
        key_id=settings.razorpay_key_id, key_secret=settings.razorpay_key_secret
    )


_COUPON_ERROR_STATUS: dict[type[Exception], int] = {
    CouponNotFoundError: status.HTTP_404_NOT_FOUND,
    CouponInactiveError: status.HTTP_400_BAD_REQUEST,
    CouponExpiredError: status.HTTP_400_BAD_REQUEST,
    CouponRedemptionLimitReachedError: status.HTTP_400_BAD_REQUEST,
    CouponNotEligibleForPlanError: status.HTTP_400_BAD_REQUEST,
    CouponAlreadyRedeemedError: status.HTTP_409_CONFLICT,
    CouponWrongTypeForActionError: status.HTTP_400_BAD_REQUEST,
}


def _map_coupon_error(exc: Exception) -> HTTPException:
    return HTTPException(_COUPON_ERROR_STATUS[type(exc)], str(exc))


async def _enforce_coupon_rate_limit(redis_client: Redis, request: Request) -> None:
    """THREAT_MODEL.md T65 -- coupon farming via disposable accounts sidesteps the
    per-account uniqueness constraint by using many real accounts, so the limit keys
    on source IP (same shape as `auth/api.py`'s login limiter) rather than account_id,
    to slow a scripted account-creation-and-redeem loop."""
    ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(redis_client, bucket="coupon_redemption", identifier=ip)
    except RateLimitExceededError as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please try again later."
        ) from exc


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
    request: Request,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> TopUpOut:
    if payload.coupon_code is not None:
        await _enforce_coupon_rate_limit(redis_client, request)
    try:
        razorpay_order_id, amount_smallest_unit = await create_topup_checkout(
            session,
            account_id=account_id,
            pack_slug=payload.pack_slug,
            currency=payload.currency,
            coupon_code=payload.coupon_code,
            gateway=_gateway(),
        )
    except CreditPackNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credit pack not found") from exc
    except CurrencyNotAvailableError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except (
        CouponNotFoundError,
        CouponInactiveError,
        CouponExpiredError,
        CouponRedemptionLimitReachedError,
        CouponNotEligibleForPlanError,
        CouponAlreadyRedeemedError,
        CouponWrongTypeForActionError,
    ) as exc:
        raise _map_coupon_error(exc) from exc
    return TopUpOut(
        razorpay_order_id=razorpay_order_id,
        razorpay_key_id=get_settings().razorpay_key_id,
        amount_smallest_unit=amount_smallest_unit,
        currency=payload.currency,
    )


@router.post("/redeem-coupon", response_model=CreditBalanceOut, status_code=status.HTTP_201_CREATED)
async def redeem_coupon_route(
    payload: RedeemCouponIn,
    request: Request,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> CreditBalanceOut:
    """`CREDIT_GRANT` coupons only (`BILLING_SYSTEM_ARCHITECTURE.md` §7.3) -- a
    `PERCENTAGE`/`FIXED_AMOUNT` code returns `400` here, apply it via `coupon_code` on
    `POST /billing/topup` instead."""
    await _enforce_coupon_rate_limit(redis_client, request)
    try:
        balance = await redeem_credit_grant_coupon(
            session, account_id=account_id, code=payload.code
        )
    except (
        CouponNotFoundError,
        CouponInactiveError,
        CouponExpiredError,
        CouponRedemptionLimitReachedError,
        CouponNotEligibleForPlanError,
        CouponAlreadyRedeemedError,
        CouponWrongTypeForActionError,
    ) as exc:
        raise _map_coupon_error(exc) from exc
    return CreditBalanceOut.model_validate(balance)


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
