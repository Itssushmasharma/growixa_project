"""Platform-admin email-validation provider config tests (GRX-SAAS-016 follow-up).

Integration-tier: exercises real Postgres and the real create_app() app, same pattern as
test_platform_ai_config.py.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.db import async_session_factory
from growixa_api.email_validation.models import PlatformEmailValidationProviderConfig
from growixa_api.email_validation.providers.base import ProviderVerificationResult
from growixa_api.platform_admin import api as platform_admin_api
from growixa_api.platform_auth.models import PlatformAdmin
from tests.conftest import DEFAULT_TEST_PASSWORD


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one()


async def _platform_login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(PlatformEmailValidationProviderConfig))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_config_returns_null_when_nothing_is_configured(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/email-validation-config")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_owner_can_set_and_read_back_the_platform_vendor(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            put_response = await client.put(
                "/platform/email-validation-config",
                json={"provider": "CLEAROUT", "api_key": "co-fake-key"},
            )
            assert put_response.status_code == 200
            body = put_response.json()
            assert body["provider"] == "CLEAROUT"
            assert body["is_active"] is True
            assert "api_key" not in body
            assert "api_key_encrypted" not in body

            get_response = await client.get("/platform/email-validation-config")
            assert get_response.json()["provider"] == "CLEAROUT"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setting_a_new_vendor_deactivates_the_previous_one(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            await client.put(
                "/platform/email-validation-config",
                json={"provider": "CLEAROUT", "api_key": "co-fake-key-1"},
            )
            await client.put(
                "/platform/email-validation-config",
                json={"provider": "CLEAROUT", "api_key": "co-fake-key-2"},
            )
            get_response = await client.get("/platform/email-validation-config")

        assert get_response.json()["provider"] == "CLEAROUT"

        async with async_session_factory() as session:
            rows = (
                (await session.execute(select(PlatformEmailValidationProviderConfig)))
                .scalars()
                .all()
            )
        assert len(rows) == 2
        assert sum(1 for r in rows if r.is_active) == 1
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_support_role_is_denied_validation_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/email-validation-config")

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_config_test_connection_succeeds_and_persists_nothing(
    monkeypatch: pytest.MonkeyPatch,
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    async def _fake_test_connection(**kwargs: object) -> None:
        return None

    # Direct-reference import in platform_admin/api.py (per this project's own
    # test-authoring gotcha) -- patch the importing module's own bound name, not the
    # source module's.
    monkeypatch.setattr(platform_admin_api, "test_validation_connection", _fake_test_connection)
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(
            "/platform/email-validation-config/test",
            json={"provider": "CLEAROUT", "api_key": "co-fake-key"},
        )
        get_response = await client.get("/platform/email-validation-config")

    assert response.status_code == 204
    assert get_response.json() is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_config_test_connection_failure_returns_502(
    monkeypatch: pytest.MonkeyPatch,
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    from growixa_api.email_validation.providers.base import EmailValidationProviderError

    async def _fake_test_connection(**kwargs: object) -> ProviderVerificationResult:
        raise EmailValidationProviderError("invalid api key")

    monkeypatch.setattr(platform_admin_api, "test_validation_connection", _fake_test_connection)
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(
            "/platform/email-validation-config/test",
            json={"provider": "CLEAROUT", "api_key": "co-bad-key"},
        )

    assert response.status_code == 502
    assert "invalid api key" in response.json()["detail"]
