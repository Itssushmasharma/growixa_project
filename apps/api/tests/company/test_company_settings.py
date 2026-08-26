"""Company/brand settings integration tests (GRX-COMPANY-001).

Integration-tier: exercises real Postgres, the real create_app() app (these are the real
production routes, not a throwaway test app), and the real seeded Admin/Viewer roles from
GRX-AUTH-001. company_profile/brand_profiles are true singletons (at most one row each per
DATABASE_SCHEMA.md), so every test clears both tables before and after it runs to stay
independent of test order.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.brand.models import BrandProfile
from growixa_api.company.models import CompanyProfile
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _clear_company_and_brand() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(BrandProfile))
        await session.execute(delete(CompanyProfile))
        await session.commit()


@pytest.fixture(autouse=True)
async def _clean_singleton_tables() -> AsyncGenerator[None, None]:
    await _clear_company_and_brand()
    yield
    await _clear_company_and_brand()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_save_and_view_company_profile(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    cookies = _access_token_cookie(admin_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        put_response = await client.put(
            "/company/profile",
            json={
                "name": "Growixa Inc.",
                "timezone": "UTC",
                "support_email": "support@growixa.example",
                "sender_name": "Growixa Team",
                "business_address": "123 Growth Way, San Francisco, CA",
                "description": "Growixa helps SMBs run AI-assisted email campaigns.",
            },
        )
        assert put_response.status_code == 200
        assert put_response.json()["name"] == "Growixa Inc."

        get_response = await client.get("/company/profile")

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["name"] == "Growixa Inc."
    assert body["timezone"] == "UTC"
    assert body["support_email"] == "support@growixa.example"
    assert body["sender_name"] == "Growixa Team"
    assert body["business_address"] == "123 Growth Way, San Francisco, CA"
    assert body["description"] == "Growixa helps SMBs run AI-assisted email campaigns."


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_can_view_but_not_edit_company_profile(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")
    cookies = _access_token_cookie(viewer_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        get_response = await client.get("/company/profile")
        put_response = await client.put("/company/profile", json={"name": "Should Not Save"})

    assert get_response.status_code == 200
    assert put_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_response = await client.get("/company/profile")
        put_response = await client.put("/company/profile", json={"name": "x"})

    assert get_response.status_code == 401
    assert put_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_brand_profile_requires_company_profile_first(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    cookies = _access_token_cookie(admin_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        early_response = await client.put("/brand/profile", json={"brand_voice": "Friendly"})
        assert early_response.status_code == 400

        await client.put("/company/profile", json={"name": "Growixa Inc."})

        brand_response = await client.put(
            "/brand/profile",
            json={
                "brand_voice": "Friendly",
                "forbidden_claims": ["guaranteed results"],
                "persona_tags": ["Professional", "Confident"],
                "voice_settings": {"formality": 70, "energy": 40},
            },
        )
        assert brand_response.status_code == 200
        assert brand_response.json()["brand_voice"] == "Friendly"

        get_response = await client.get("/brand/profile")

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["forbidden_claims"] == ["guaranteed results"]
    assert body["persona_tags"] == ["Professional", "Confident"]
    assert body["voice_settings"] == {"formality": 70, "energy": 40}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_can_view_but_not_edit_brand_profile(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as admin_client:
        await admin_client.put("/company/profile", json={"name": "Growixa Inc."})

    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as viewer_client:
        get_response = await viewer_client.get("/brand/profile")
        put_response = await viewer_client.put("/brand/profile", json={"brand_voice": "x"})

    assert get_response.status_code == 200
    assert put_response.status_code == 403
