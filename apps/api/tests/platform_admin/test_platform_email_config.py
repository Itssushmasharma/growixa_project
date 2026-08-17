"""Platform-admin email provider config tests.

Integration-tier: exercises real Postgres and the real create_app() app, same pattern
as test_platform_ai_config.py. The real SMTP connect/auth in the "test connection"
route is monkeypatched at platform_admin.api's own imported name (not
notifications.services', since that's a direct-reference import -- patching the
source module after import time wouldn't affect the already-bound name) -- no live
SMTP server is reachable from this test environment.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.db import async_session_factory
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.notifications.models import PlatformEmailProviderConfig
from growixa_api.platform_admin import api as platform_admin_api
from growixa_api.platform_auth.models import PlatformAdmin


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
        await session.execute(delete(PlatformEmailProviderConfig))
        await session.commit()


_VALID_PAYLOAD = {
    "provider": "POSTMARK",
    "smtp_host": "smtp.postmarkapp.com",
    "smtp_port": 587,
    "smtp_username": "server-token",
    "smtp_password": "server-token",
    "from_email": "noreply@growixa.local",
    "from_name": "Growixa",
}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_email_config_returns_null_when_nothing_is_configured(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/email-config")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_owner_can_set_and_read_back_the_platform_default(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            put_response = await client.put("/platform/email-config", json=_VALID_PAYLOAD)
            assert put_response.status_code == 200
            body = put_response.json()
            assert body["provider"] == "POSTMARK"
            assert body["smtp_host"] == "smtp.postmarkapp.com"
            assert body["is_active"] is True
            assert "smtp_password" not in body
            assert "smtp_password_encrypted" not in body

            get_response = await client.get("/platform/email-config")
            assert get_response.json()["provider"] == "POSTMARK"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setting_a_new_config_deactivates_the_previous_one(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            await client.put("/platform/email-config", json=_VALID_PAYLOAD)
            await client.put(
                "/platform/email-config",
                json={**_VALID_PAYLOAD, "provider": "CUSTOM_SMTP", "smtp_host": "smtp.other.com"},
            )
            get_response = await client.get("/platform/email-config")

        assert get_response.json()["provider"] == "CUSTOM_SMTP"

        async with async_session_factory() as session:
            rows = (await session.execute(select(PlatformEmailProviderConfig))).scalars().all()
        assert len(rows) == 2
        assert sum(1 for r in rows if r.is_active) == 1
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_support_role_is_denied_email_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Only platform.owner/platform.admin get platform.email.manage -- matches
    platform.ai.manage's higher-trust shape (gates an encrypted credential)."""
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/email-config")

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_email_config_test_connection_succeeds_and_persists_nothing(
    monkeypatch: pytest.MonkeyPatch,
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    async def _fake_test_connection(data: object) -> None:
        return None

    monkeypatch.setattr(platform_admin_api, "test_platform_email_config", _fake_test_connection)
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post("/platform/email-config/test", json=_VALID_PAYLOAD)
        get_response = await client.get("/platform/email-config")

    assert response.status_code == 204
    assert get_response.json() is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_email_config_test_connection_failure_returns_502(
    monkeypatch: pytest.MonkeyPatch,
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    async def _fake_test_connection(data: object) -> None:
        raise EmailSendError("connection refused")

    monkeypatch.setattr(platform_admin_api, "test_platform_email_config", _fake_test_connection)
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post("/platform/email-config/test", json=_VALID_PAYLOAD)

    assert response.status_code == 502
