from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.schemas import LoginIn, LoginOut
from growixa_api.auth.services import InvalidCredentialsError
from growixa_api.auth.services import login as login_service
from growixa_api.auth.services import logout as logout_service
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
