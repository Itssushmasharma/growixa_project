"""AI capability generation + history tests (GRX-AI-006/007).

Integration-tier: exercises real Postgres and the real create_app() app. The provider
call itself is monkeypatched at the get_effective_ai_provider boundary (same "mock the
external call, exercise everything else for real" convention as
test_social_posts.py's storage_client/publish_job monkeypatching) -- prompt construction,
DB writes (ai_generations + usage_records), and error classification all run for real.
No live AI provider is reachable from the host test environment.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.ai import services as ai_services
from growixa_api.ai.models import AIGeneration, AIProviderConnection, PlatformAIProviderConfig
from growixa_api.ai.providers.base import AIGenerationResult, AIProviderError
from growixa_api.ai.providers.factory import (
    AINotConfiguredError,
    ResolvedAIProvider,
    get_effective_ai_provider,
)
from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.usage.models import UsageRecord


class _FakeProvider:
    def __init__(self, *, text: str = "Fake generated text", fail: bool = False) -> None:
        self._text = text
        self._fail = fail

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        if self._fail:
            raise AIProviderError("fake provider failure")
        return AIGenerationResult(text=self._text, prompt_tokens=10, completion_tokens=5)


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AIGeneration))
        await session.execute(
            delete(UsageRecord).where(UsageRecord.operation_type == "ai_generation")
        )
        await session.execute(delete(AIProviderConnection))
        await session.execute(delete(PlatformAIProviderConfig))
        await session.commit()


@pytest.fixture
async def ai_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


def _patch_provider(monkeypatch: pytest.MonkeyPatch, provider: _FakeProvider) -> None:
    async def _fake_get_effective_ai_provider(
        session: object, account_id: uuid.UUID
    ) -> ResolvedAIProvider:
        return ResolvedAIProvider(
            provider=provider,
            provider_name="OPENAI",
            model="gpt-4o-mini",
            source="PLATFORM_DEFAULT",
        )

    monkeypatch.setattr(ai_services, "get_effective_ai_provider", _fake_get_effective_ai_provider)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai_manage_can_generate_a_subject_line(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    _patch_provider(monkeypatch, _FakeProvider(text="20% Off Running Shoes!"))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "a running shoe sale"}
            )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "COMPLETE"
        assert body["output"] == {"text": "20% Off Running Shoes!"}
        assert body["prompt_tokens"] == 10
        assert body["completion_tokens"] == 5
        assert body["provider"] == "OPENAI"

        async with async_session_factory() as session:
            usage_rows = (
                (
                    await session.execute(
                        select(UsageRecord).where(UsageRecord.operation_type == "ai_generation")
                    )
                )
                .scalars()
                .all()
            )
        assert len(usage_rows) == 1
        assert usage_rows[0].quantity == 15
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_a_provider_failure_writes_a_failed_row_and_no_usage_record(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    _patch_provider(monkeypatch, _FakeProvider(fail=True))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "a running shoe sale"}
            )

        assert response.status_code == 502

        async with async_session_factory() as session:
            generations = (await session.execute(select(AIGeneration))).scalars().all()
            usage_rows = (
                (
                    await session.execute(
                        select(UsageRecord).where(UsageRecord.operation_type == "ai_generation")
                    )
                )
                .scalars()
                .all()
            )
        assert len(generations) == 1
        assert generations[0].status == "FAILED"
        assert generations[0].error_message == "fake provider failure"
        assert usage_rows == []
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_with_no_provider_configured_returns_409_and_writes_no_row(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "a running shoe sale"}
            )

        assert response.status_code == 409

        async with async_session_factory() as session:
            generations = (await session.execute(select(AIGeneration))).scalars().all()
        assert generations == []
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_content_creator_can_generate_but_not_publish_anything(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    """Content Creator holds ai.manage but never campaigns.send/social.publish -- this
    route has no code path that could send/publish regardless (DEC-GRX-006)."""
    _patch_provider(monkeypatch, _FakeProvider())
    creator_id = await user_factory(
        full_name="Content Creator", role_name="Content Creator", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(creator_id)
        ) as client:
            response = await client.post("/ai/generate/HASHTAGS", json={"brief": "running shoes"})
        assert response.status_code == 200
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_can_view_but_not_generate(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    _patch_provider(monkeypatch, _FakeProvider())
    analyst_id = await user_factory(
        full_name="Analyst", role_name="Analyst", account_id=ai_account_id
    )
    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        generate_response = await client.post(
            "/ai/generate/HASHTAGS", json={"brief": "running shoes"}
        )
        history_response = await client.get("/ai/generations")

    assert generate_response.status_code == 403
    assert history_response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_gets_403_on_both_generate_and_history(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    viewer_id = await user_factory(full_name="Viewer", role_name="Viewer", account_id=ai_account_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        generate_response = await client.post(
            "/ai/generate/HASHTAGS", json={"brief": "running shoes"}
        )
        history_response = await client.get("/ai/generations")

    assert generate_response.status_code == 403
    assert history_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generation_history_list_and_capability_filter(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    ai_account_id: uuid.UUID,
) -> None:
    _patch_provider(monkeypatch, _FakeProvider())
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=ai_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            await client.post("/ai/generate/SUBJECT_LINE", json={"brief": "a sale"})
            await client.post("/ai/generate/HASHTAGS", json={"brief": "a sale"})

            all_response = await client.get("/ai/generations")
            filtered_response = await client.get("/ai/generations?capability=HASHTAGS")

        assert len(all_response.json()) == 2
        filtered = filtered_response.json()
        assert len(filtered) == 1
        assert filtered[0]["capability"] == "HASHTAGS"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_byo_connection_takes_precedence_over_platform_default(
    ai_account_id: uuid.UUID,
) -> None:
    """Resolution order per DEC-GRX-026: the account's own active connection wins over
    the platform default when both exist."""

    async with async_session_factory() as session:
        session.add(
            PlatformAIProviderConfig(
                provider="ANTHROPIC",
                api_key_encrypted=encrypt_secret("platform-fake-key"),
                default_model="claude-sonnet-4-5",
            )
        )
        session.add(
            AIProviderConnection(
                account_id=ai_account_id,
                provider="OPENAI",
                api_key_encrypted=encrypt_secret("byo-fake-key"),
                default_model="gpt-4o-mini",
            )
        )
        await session.commit()

    try:
        async with async_session_factory() as session:
            resolved = await get_effective_ai_provider(session, ai_account_id)
        assert resolved.provider_name == "OPENAI"
        assert resolved.model == "gpt-4o-mini"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_default_used_when_no_byo_connection_exists(
    ai_account_id: uuid.UUID,
) -> None:

    async with async_session_factory() as session:
        session.add(
            PlatformAIProviderConfig(
                provider="ANTHROPIC",
                api_key_encrypted=encrypt_secret("platform-fake-key"),
                default_model="claude-sonnet-4-5",
            )
        )
        await session.commit()

    try:
        async with async_session_factory() as session:
            resolved = await get_effective_ai_provider(session, ai_account_id)
        assert resolved.provider_name == "ANTHROPIC"
        assert resolved.model == "claude-sonnet-4-5"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_no_provider_configured_raises_ai_not_configured_error(
    ai_account_id: uuid.UUID,
) -> None:

    async with async_session_factory() as session:
        with pytest.raises(AINotConfiguredError):
            await get_effective_ai_provider(session, ai_account_id)
