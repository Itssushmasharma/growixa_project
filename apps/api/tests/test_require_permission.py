"""require_permission() dependency tests (GRX-RBAC-001).

Integration-tier: exercises real Postgres (the Sprint 1 seeded roles/permissions from
GRX-AUTH-001) and a hand-minted JWT using the same signing-key config that GRX-AUTH-002's
login flow will use to issue real access-token cookies later.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from growixa_api.config import get_settings
from growixa_api.permissions.dependencies import require_permission


def _make_protected_app(permission_code: str) -> FastAPI:
    app = FastAPI()
    permission_dependency = require_permission(permission_code)

    @app.get("/protected")
    async def protected(user_id: uuid.UUID = Depends(permission_dependency)) -> dict[str, str]:
        return {"user_id": str(user_id)}

    return app


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_with_permission_is_allowed(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    # Viewer has company.settings.view per RBAC.md's Sprint 1 matrix.
    viewer_user_id = await user_factory(full_name="Test Viewer", role_name="Viewer")
    transport = ASGITransport(app=_make_protected_app("company.settings.view"))
    cookies = _access_token_cookie(viewer_user_id)
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"user_id": str(viewer_user_id)}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_without_permission_is_forbidden(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    # Viewer does NOT have users.manage per RBAC.md's Sprint 1 matrix.
    viewer_user_id = await user_factory(full_name="Test Viewer", role_name="Viewer")
    transport = ASGITransport(app=_make_protected_app("users.manage"))
    cookies = _access_token_cookie(viewer_user_id)
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.get("/protected")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_token_is_unauthorized() -> None:
    transport = ASGITransport(app=_make_protected_app("company.settings.view"))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/protected")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_is_unauthorized() -> None:
    transport = ASGITransport(app=_make_protected_app("company.settings.view"))
    cookies = {"access_token": "not-a-real-token"}
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.get("/protected")

    assert response.status_code == 401
