"""Platform-admin AI provider config tests (GRX-AI-005).

Integration-tier: exercises real Postgres and the real create_app() app, same pattern as
test_platform_admin_usage.py.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.ai import services as ai_services
from growixa_api.ai.models import PlatformAIProviderConfig
from growixa_api.ai.providers.base import AIGenerationResult
from growixa_api.app import create_app
from growixa_api.db import async_session_factory
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
        await session.execute(delete(PlatformAIProviderConfig))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_ai_config_returns_null_when_nothing_is_configured(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/ai-config")

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
            put_response = await client.put(
                "/platform/ai-config",
                json={
                    "provider": "ANTHROPIC",
                    "api_key": "sk-fake",
                    "default_model": "claude-sonnet-4-5",
                },
            )
            assert put_response.status_code == 200
            body = put_response.json()
            assert body["provider"] == "ANTHROPIC"
            assert body["is_active"] is True
            assert "api_key" not in body
            assert "api_key_encrypted" not in body

            get_response = await client.get("/platform/ai-config")
            assert get_response.json()["provider"] == "ANTHROPIC"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_setting_a_new_default_deactivates_the_previous_one(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            await client.put(
                "/platform/ai-config",
                json={"provider": "OPENAI", "api_key": "sk-fake-1", "default_model": "gpt-4o-mini"},
            )
            await client.put(
                "/platform/ai-config",
                json={
                    "provider": "ANTHROPIC",
                    "api_key": "sk-fake-2",
                    "default_model": "claude-sonnet-4-5",
                },
            )
            get_response = await client.get("/platform/ai-config")

        assert get_response.json()["provider"] == "ANTHROPIC"

        async with async_session_factory() as session:
            rows = (await session.execute(select(PlatformAIProviderConfig))).scalars().all()
        assert len(rows) == 2
        assert sum(1 for r in rows if r.is_active) == 1
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ollama_config_with_a_private_ip_base_url_is_rejected(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.put(
            "/platform/ai-config",
            json={
                "provider": "OLLAMA",
                "base_url": "http://10.0.0.5:11434",
                "default_model": "llama3",
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_support_role_is_denied_ai_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Per this task's design, only platform.owner/platform.admin get
    platform.ai.manage -- platform.support/finance/operations must 403, matching
    platform.accounts.manage's higher-trust shape (this gates an encrypted credential,
    not just an operational view)."""
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/ai-config")

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai_config_test_connection_succeeds_and_persists_nothing(
    monkeypatch: pytest.MonkeyPatch,
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    async def _fake_test_connection(**kwargs: object) -> AIGenerationResult:
        return AIGenerationResult(text="OK", prompt_tokens=5, completion_tokens=1)

    monkeypatch.setattr(ai_services.factory, "test_connection", _fake_test_connection)
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(
            "/platform/ai-config/test",
            json={"provider": "OPENAI", "api_key": "sk-fake", "default_model": "gpt-4o-mini"},
        )
        get_response = await client.get("/platform/ai-config")

    assert response.status_code == 204
    assert get_response.json() is None
