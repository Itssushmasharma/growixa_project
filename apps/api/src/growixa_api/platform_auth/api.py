import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.rate_limit import RateLimitExceededError, enforce_rate_limit
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.platform_auth.dependencies import get_current_platform_admin_id
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.platform_auth.repositories import list_permission_codes_for_platform_admin
from growixa_api.platform_auth.schemas import PlatformLoginIn, PlatformLoginOut, PlatformMeOut
from growixa_api.platform_auth.services import InvalidPlatformCredentialsError
from growixa_api.platform_auth.services import login as login_service
from growixa_api.redis import get_redis

_RATE_LIMIT_MESSAGE = "Too many attempts. Please try again later."

router = APIRouter(prefix="/platform/auth", tags=["platform_auth"])

_PLATFORM_ACCESS_TOKEN_COOKIE = "platform_access_token"


def _set_platform_auth_cookie(
    response: Response, access_token: str, request: Request | None = None
) -> None:
    settings = get_settings()
    is_https = False
    if request:
        is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    secure = is_https and settings.environment not in ("local", "test")
    samesite: Literal["lax", "none"] = "none" if secure else "lax"
    response.set_cookie(
        _PLATFORM_ACCESS_TOKEN_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.access_token_ttl_minutes * 60,
        path="/",
    )


@router.post("/login", response_model=PlatformLoginOut)
async def platform_login_route(
    payload: PlatformLoginIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis),
) -> PlatformLoginOut:
    rate_limit_ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(
            redis_client, bucket="platform_login", identifier=f"{payload.email}:{rate_limit_ip}"
        )
    except RateLimitExceededError as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _RATE_LIMIT_MESSAGE) from exc

    try:
        result = await login_service(session, email=payload.email, password=payload.password)
    except InvalidPlatformCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from exc

    _set_platform_auth_cookie(response, result.access_token, request=request)
    return PlatformLoginOut.model_validate(result.admin)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def platform_logout_route(response: Response) -> None:
    # No server-side session to revoke -- Phase B deliberately ships no refresh-token
    # rotation for platform admins (see MASTER_TASK_TRACKER.md's GRX-SAAS-002 evidence),
    # so logout is just clearing the cookie, same shape as a plain access-token-only login.
    settings = get_settings()
    secure = settings.environment not in ("local", "test")
    samesite: Literal["lax", "none"] = "none" if secure else "lax"
    response.delete_cookie(
        _PLATFORM_ACCESS_TOKEN_COOKIE, secure=secure, samesite=samesite, path="/"
    )


@router.get("/me", response_model=PlatformMeOut)
async def platform_me_route(
    platform_admin_id: uuid.UUID = Depends(get_current_platform_admin_id),
    session: AsyncSession = Depends(get_session),
) -> PlatformMeOut:
    """Identifies the current session via the platform access-token cookie itself, not
    require_platform_permission() -- any authenticated platform admin may know who they
    are, same reasoning as auth/api.py's /auth/me."""
    admin = await session.get(PlatformAdmin, platform_admin_id)
    if admin is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    permissions = await list_permission_codes_for_platform_admin(session, platform_admin_id)
    return PlatformMeOut(
        id=admin.id,
        email=admin.email,
        full_name=admin.full_name,
        role=admin.role,
        permissions=sorted(permissions),
    )
