from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.schemas import RegisterIn, RegisterOut, VerifyEmailIn
from growixa_api.accounts.services import EmailAlreadyRegisteredError, InvalidVerificationTokenError
from growixa_api.accounts.services import register as register_service
from growixa_api.accounts.services import verify_email as verify_email_service
from growixa_api.auth.rate_limit import RateLimitExceededError, enforce_rate_limit
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.redis import get_redis

_RATE_LIMIT_MESSAGE = "Too many attempts. Please try again later."

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED)
async def register_route(
    payload: RegisterIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> RegisterOut:
    rate_limit_ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(
            redis_client, bucket="register", identifier=f"{payload.email}:{rate_limit_ip}"
        )
    except RateLimitExceededError as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _RATE_LIMIT_MESSAGE) from exc

    try:
        result, raw_token = await register_service(
            session,
            account_name=payload.account_name,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            plan_slug=payload.plan_slug,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A user with this email already exists"
        ) from exc

    token = raw_token if get_settings().environment in ("local", "test") else None
    return RegisterOut(
        account_id=result.account.id,
        user_id=result.user.id,
        email=result.user.email,
        message="Account created. Check your email to verify and activate your account.",
        token=token,
    )


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email_route(
    payload: VerifyEmailIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> None:
    rate_limit_ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(redis_client, bucket="verify_email", identifier=rate_limit_ip)
    except RateLimitExceededError as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _RATE_LIMIT_MESSAGE) from exc

    try:
        await verify_email_service(session, raw_token=payload.token)
    except InvalidVerificationTokenError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or expired verification token"
        ) from exc
