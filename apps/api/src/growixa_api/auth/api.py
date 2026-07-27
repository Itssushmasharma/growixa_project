from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.schemas import (
    LoginIn,
    LoginOut,
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

router = APIRouter(prefix="/auth", tags=["auth"])

_ACCESS_TOKEN_COOKIE = "access_token"
_REFRESH_TOKEN_COOKIE = "refresh_token"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    # Secure requires HTTPS to be sent back by the browser; local dev runs over plain HTTP.
    # HttpOnly + SameSite=Lax apply unconditionally per AUTHENTICATION.md.
    secure = settings.environment != "local"
    response.set_cookie(
        _ACCESS_TOKEN_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.access_token_ttl_minutes * 60,
    )
    response.set_cookie(
        _REFRESH_TOKEN_COOKIE,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
    )


@router.post("/login", response_model=LoginOut)
async def login_route(
    payload: LoginIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginOut:
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

    _set_auth_cookies(response, result.access_token, result.refresh_token)
    return LoginOut.model_validate(result.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_route(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> None:
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    await logout_service(session, raw_refresh_token=raw_refresh_token)
    response.delete_cookie(_ACCESS_TOKEN_COOKIE)
    response.delete_cookie(_REFRESH_TOKEN_COOKIE)


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

    _set_auth_cookies(response, result.access_token, result.refresh_token)
    return LoginOut.model_validate(result.user)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_route(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> None:
    raw_refresh_token = request.cookies.get(_REFRESH_TOKEN_COOKIE)
    await logout_all_service(session, raw_refresh_token=raw_refresh_token)
    response.delete_cookie(_ACCESS_TOKEN_COOKIE)
    response.delete_cookie(_REFRESH_TOKEN_COOKIE)


_PASSWORD_RESET_REQUESTED_MESSAGE = (
    "If an account with that email exists, a password reset link has been sent."
)


@router.post("/password-reset/request", response_model=PasswordResetRequestOut)
async def password_reset_request_route(
    payload: PasswordResetRequestIn,
    session: AsyncSession = Depends(get_session),
) -> PasswordResetRequestOut:
    raw_token = await request_password_reset_service(session, email=payload.email)

    # Response is identical for a known vs. unknown email — per THREAT_MODEL.md T11 — with
    # the raw token echoed back only in local dev, where no email-delivery channel exists.
    token = raw_token if get_settings().environment == "local" else None
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
