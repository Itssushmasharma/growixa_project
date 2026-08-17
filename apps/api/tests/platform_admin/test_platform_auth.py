"""Platform admin auth boundary tests (GRX-SAAS-002 Phase B).

Integration-tier: exercises real Postgres and the real create_app() app. Covers the
Phase B acceptance criteria directly: a platform-admin session works end to end, and a
platform-admin cookie is never accepted by a customer route (and vice versa) -- both
directions 401, per SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md's Phase B acceptance
criteria and THREAT_MODEL.md's T20.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin
from tests.conftest import DEFAULT_TEST_PASSWORD


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one()


def _customer_access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


def _platform_access_token_cookie(platform_admin_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode(
        {"sub": str(platform_admin_id)}, get_settings().jwt_signing_key, algorithm="HS256"
    )
    return {"platform_access_token": token}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_admin_can_login_and_fetch_me(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(full_name="Owner Admin", role="platform.owner")
    email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        body = login_response.json()
        assert body["id"] == str(admin_id)
        assert body["email"] == email
        assert body["role"] == "platform.owner"
        assert client.cookies.get("platform_access_token") is not None

        me_response = await client.get("/platform/auth/me")

    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["id"] == str(admin_id)
    assert me_body["role"] == "platform.owner"
    assert "platform.access" in me_body["permissions"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_platform_credentials_return_401(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(full_name="Wrong Password Admin")
    email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/platform/auth/login", json={"email": email, "password": "definitely-wrong"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_disabled_platform_admin_cannot_login(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(full_name="Disabled Admin", status="DISABLED")
    email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_logout_clears_the_session(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(full_name="Logout Admin")
    email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200

        logout_response = await client.post("/platform/auth/logout")
        assert logout_response.status_code == 204

        me_response = await client.get("/platform/auth/me")

    assert me_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_admin_cookie_is_rejected_by_customer_auth_me_route(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """A platform-admin session cookie must never be accepted by a customer /auth/*
    route -- Phase B's own acceptance criterion, both directions 401."""
    admin_id = await platform_admin_factory(full_name="Cross Boundary Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies=_platform_access_token_cookie(admin_id),
    ) as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_customer_cookie_is_rejected_by_platform_me_route(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """The reverse direction of the same acceptance criterion: a customer session
    cookie must never be accepted by a platform-only route."""
    user_id = await user_factory(full_name="Cross Boundary User")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_customer_access_token_cookie(user_id)
    ) as client:
        response = await client.get("/platform/auth/me")

    assert response.status_code == 401
