import uuid

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.platform_auth.repositories import platform_admin_has_permission

_JWT_ALGORITHM = "HS256"
_PLATFORM_ACCESS_TOKEN_COOKIE = "platform_access_token"


async def get_current_platform_admin_id(request: Request) -> uuid.UUID:
    """Resolve the identity behind the platform-admin access-token cookie.

    Structurally separate from permissions.dependencies.get_current_user_id: a
    different cookie name (`platform_access_token` vs `access_token`) means a customer
    session can never satisfy this dependency and vice versa -- see RBAC.md's Sprint 5
    Phase B section and THREAT_MODEL.md's T20. Same JWT signing key/algorithm as the
    customer side (both are the "existing JWT/HttpOnly-cookie mechanism" per
    SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md's Phase B scope), but this never checks the
    `users`/`accounts` tables -- only `platform_admins`.
    """
    token = request.cookies.get(_PLATFORM_ACCESS_TOKEN_COOKIE)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        payload = jwt.decode(token, get_settings().jwt_signing_key, algorithms=[_JWT_ALGORITHM])
        return uuid.UUID(str(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated") from exc


class RequirePlatformPermission:
    """Callable FastAPI dependency: 401s if unauthenticated, 403s if lacking `code`.

    Deliberately a distinct class from permissions.dependencies.RequirePermission --
    accidentally using the wrong one on a route is exactly the kind of bug that must be
    structurally hard to make (GRX-SAAS-002), not just documented against. A class
    (not a closure) so a route-protection audit test can isinstance()-check it, same
    pattern as RequirePermission -- see test_protected_routes_audit.py.
    """

    def __init__(self, code: str) -> None:
        self.code = code

    async def __call__(
        self,
        platform_admin_id: uuid.UUID = Depends(get_current_platform_admin_id),
        session: AsyncSession = Depends(get_session),
    ) -> uuid.UUID:
        if not await platform_admin_has_permission(session, platform_admin_id, self.code):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permission")
        return platform_admin_id


def require_platform_permission(code: str) -> RequirePlatformPermission:
    return RequirePlatformPermission(code)
