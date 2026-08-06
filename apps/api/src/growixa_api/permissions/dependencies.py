import uuid

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.repositories import get_account_id_for_user
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.permissions.repositories import user_has_permission

_JWT_ALGORITHM = "HS256"


async def get_current_user_id(request: Request) -> uuid.UUID:
    """Resolve the identity behind the access-token cookie.

    This is the verify-only half of token handling: it proves a presented token is valid
    and extracts the user id, but nothing issues that cookie yet — that is GRX-AUTH-002's
    login flow. Lives here (not in a not-yet-existing `auth` module) because
    require_permission() cannot function without some way to identify the caller, and
    GRX-RBAC-001 depends only on GRX-AUTH-001.
    """
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        payload = jwt.decode(token, get_settings().jwt_signing_key, algorithms=[_JWT_ALGORITHM])
        return uuid.UUID(str(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated") from exc


async def get_current_account_id(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    """Resolves the caller's account_id from their own user row (GRX-SAAS-001).

    Not embedded in the JWT -- the token payload stays `{"sub": user_id}` unchanged, and
    this does one extra lookup per request, matching the existing precedent of
    RequirePermission doing its own DB round-trip rather than trusting client-supplied
    claims for anything authorization-relevant.
    """
    account_id = await get_account_id_for_user(session, user_id)
    if account_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return account_id


class RequirePermission:
    """Callable FastAPI dependency: 401s if unauthenticated, 403s if lacking `code`.

    A class (rather than a closure) so a route-protection audit can `isinstance()`-check a
    route's dependencies to confirm every non-public route is actually guarded — see
    test_protected_routes_audit.py.
    """

    def __init__(self, code: str) -> None:
        self.code = code

    async def __call__(
        self,
        user_id: uuid.UUID = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
    ) -> uuid.UUID:
        if not await user_has_permission(session, user_id, self.code):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permission")
        return user_id


def require_permission(code: str) -> RequirePermission:
    return RequirePermission(code)
