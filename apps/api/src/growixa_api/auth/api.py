import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.rate_limit import RateLimitExceededError, enforce_rate_limit
from growixa_api.auth.schemas import (
    LoginIn,
    LoginOut,
    MeOut,
    PasswordResetCompleteIn,
    PasswordResetRequestIn,
    PasswordResetRequestOut,
)
from growixa_api.auth.services import (
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
)
from growixa_api.auth.services import complete_password_reset as complete_password_reset_service
from growixa_api.auth.services import login as login_service
from growixa_api.auth.services import logout as logout_service
from growixa_api.auth.services import logout_all as logout_all_service
from growixa_api.auth.services import refresh as refresh_service
from growixa_api.auth.services import request_password_reset as request_password_reset_service
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_user_id
from growixa_api.permissions.repositories import list_permission_codes_for_user
from growixa_api.redis import get_redis
from growixa_api.users.models import User

_RATE_LIMIT_MESSAGE = "Too many attempts. Please try again later."

router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_TOKEN_COOKIE = "access_token"
_REFRESH_TOKEN_COOKIE = "refresh_token"


def _set_auth_cookies(
    response: Response, access_token: str, refresh_token: str, request: Request | None = None
) -> None:
    settings = get_settings()
    is_https = False
    if request:
        is_https = (
            request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        )
    secure = is_https and settings.environment not in ("local", "test")
    samesite: Literal["lax", "none"] = "none" if secure else "lax"
    response.set_cookie(
        _ACCESS_TOKEN_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.access_token_ttl_minutes * 60,
        path="/",
    )
    response.set_cookie(
        _REFRESH_TOKEN_COOKIE,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        path="/",
    )


@router.post("/login", response_model=LoginOut)
async def login_route(
    payload: LoginIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> LoginOut:
    rate_limit_ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(
            redis_client, bucket="login", identifier=f"{payload.email}:{rate_limit_ip}"
        )
    except RateLimitExceededError as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _RATE_LIMIT_MESSAGE) from exc

    try:
        result = await login_service(
            session,
            email=payload.email,
            password=payload.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from exc

    _set_auth_cookies(response, result.access_token, result.refresh_token, request=request)
    return LoginOut.model_validate(result.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_route(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> None:
    settings = get_settings()
    secure = settings.environment not in ("local", "test")
    samesite: Literal["lax", "none"] = "none" if secure else "lax"
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    await logout_service(session, raw_refresh_token=raw_refresh_token)
    response.delete_cookie(_ACCESS_TOKEN_COOKIE, secure=secure, samesite=samesite, path="/")
    response.delete_cookie(_REFRESH_TOKEN_COOKIE, secure=secure, samesite=samesite, path="/")


@router.post("/refresh", response_model=LoginOut)
async def refresh_route(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginOut:
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    try:
        result = await refresh_service(
            session,
            raw_refresh_token=raw_refresh_token,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token"
        ) from exc

    _set_auth_cookies(response, result.access_token, result.refresh_token, request=request)
    return LoginOut.model_validate(result.user)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_route(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> None:
    settings = get_settings()
    secure = settings.environment not in ("local", "test")
    samesite: Literal["lax", "none"] = "none" if secure else "lax"
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    await logout_all_service(session, raw_refresh_token=raw_refresh_token)
    response.delete_cookie(_ACCESS_TOKEN_COOKIE, secure=secure, samesite=samesite, path="/")
    response.delete_cookie(_REFRESH_TOKEN_COOKIE, secure=secure, samesite=samesite, path="/")


@router.get("/me", response_model=MeOut)
async def me_route(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> MeOut:
    """Identifies the current session, the same way /refresh and /logout-all do — via the
    access-token cookie itself, not require_permission(). Any authenticated user may know
    who they are; there is no separate permission for it."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    permissions = await list_permission_codes_for_user(session, user_id)
    return MeOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        permissions=sorted(permissions),
    )


_PASSWORD_RESET_REQUESTED_MESSAGE = (
    "If an account with that email exists, a password reset link has been sent."
)


@router.post("/password-reset/request", response_model=PasswordResetRequestOut)
async def password_reset_request_route(
    payload: PasswordResetRequestIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> PasswordResetRequestOut:
    rate_limit_ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(
            redis_client,
            bucket="password_reset_request",
            identifier=f"{payload.email}:{rate_limit_ip}",
        )
    except RateLimitExceededError as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _RATE_LIMIT_MESSAGE) from exc

    raw_token = await request_password_reset_service(session, email=payload.email)

    # Response is identical for a known vs. unknown email — per THREAT_MODEL.md T11 — with
    # the raw token echoed back only in local dev and the pytest suite, neither of which has
    # a real email-delivery channel (same "local" vs. "test" reasoning as _set_auth_cookies'
    # secure-cookie decision above).
    token = raw_token if get_settings().environment in ("local", "test") else None
    return PasswordResetRequestOut(message=_PASSWORD_RESET_REQUESTED_MESSAGE, token=token)


@router.post("/password-reset/complete", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_complete_route(
    payload: PasswordResetCompleteIn,
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await complete_password_reset_service(
            session, raw_token=payload.token, new_password=payload.new_password
        )
    except InvalidPasswordResetTokenError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or expired password reset token"
        ) from exc
