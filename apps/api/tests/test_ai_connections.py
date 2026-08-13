"""Account bring-your-own AI provider connection tests (GRX-AI-004).

Integration-tier: exercises real Postgres and the real create_app() app, same convention
as test_social_posts.py. No real provider credentials are used here -- api_key values
are throwaway strings, since this file verifies the connection CRUD/validation logic,
not any provider's own API.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.ai.models import AIProviderConnection
from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AIProviderConnection))
        await session.commit()


@pytest.fixture
async def ai_account_id(account_factory: Callable[..., Awaitable[uuid.UUID]]) -> uuid.UUID:
    return await account_factory()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_super_admin_can_create_list_and_deactivate_a_connection(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    admin_id = await user_factory(
        full_name="Super Admin", role_name="Super Admin", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            create_response = await client.post(
                "/ai/connections",
                json={"provider": "OPENAI", "api_key": "sk-fake", "default_model": "gpt-4o-mini"},
            )
            assert create_response.status_code == 201
            body = create_response.json()
            assert body["provider"] == "OPENAI"
            assert body["is_active"] is True
            assert "api_key" not in body
            assert "api_key_encrypted" not in body
            connection_id = body["id"]

            list_response = await client.get("/ai/connections")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 1

            deactivate_response = await client.post(f"/ai/connections/{connection_id}/deactivate")
            assert deactivate_response.status_code == 200
            assert deactivate_response.json()["is_active"] is False

            list_after_response = await client.get("/ai/connections")
            assert list_after_response.json() == []
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_creating_a_second_connection_deactivates_the_first(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    admin_id = await user_factory(
        full_name="Super Admin", role_name="Super Admin", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            await client.post(
                "/ai/connections",
                json={"provider": "OPENAI", "api_key": "sk-fake-1", "default_model": "gpt-4o-mini"},
            )
            await client.post(
                "/ai/connections",
                json={
                    "provider": "ANTHROPIC",
                    "api_key": "sk-fake-2",
                    "default_model": "claude-sonnet-4-5",
                },
            )

            list_response = await client.get("/ai/connections")
            connections = list_response.json()

        assert len(connections) == 1
        assert connections[0]["provider"] == "ANTHROPIC"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_azure_openai_connection_without_base_url_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    admin_id = await user_factory(
        full_name="Super Admin", role_name="Super Admin", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.post(
                "/ai/connections",
                json={"provider": "AZURE_OPENAI", "api_key": "fake", "default_model": "gpt4"},
            )
        assert response.status_code == 400
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ollama_connection_with_a_metadata_ip_base_url_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    admin_id = await user_factory(
        full_name="Super Admin", role_name="Super Admin", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.post(
                "/ai/connections",
                json={
                    "provider": "OLLAMA",
                    "base_url": "http://169.254.169.254/",
                    "default_model": "llama3",
                },
            )
        assert response.status_code == 400
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_super_admin_role_is_denied_connection_management(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    """integrations.manage is Super-Admin-only -- Admin (which gets almost everything
    else) is deliberately excluded, matching email_provider_connections' shape."""
    admin_id = await user_factory(full_name="Admin", role_name="Admin", account_id=ai_account_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        list_response = await client.get("/ai/connections")
        create_response = await client.post(
            "/ai/connections",
            json={"provider": "OPENAI", "api_key": "sk-fake", "default_model": "gpt-4o-mini"},
        )

    assert list_response.status_code == 403
    assert create_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deactivating_an_unknown_connection_404s(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    admin_id = await user_factory(
        full_name="Super Admin", role_name="Super Admin", account_id=ai_account_id
    )
    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(f"/ai/connections/{uuid.uuid4()}/deactivate")

    assert response.status_code == 404
