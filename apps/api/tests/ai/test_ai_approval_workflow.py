"""Human-manager approval workflow tests (Phase 5, GRX-AI-006).

Tests cover approve, reject, and edit sub-resource actions on ai_generations.
Convention mirrors test_ai_generate.py: real Postgres + real app + monkeypatched
provider. Approval routes require ai.review permission; generation requires
ai.manage.
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
from growixa_api.ai.providers.factory import ResolvedAIProvider
from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.usage.models import UsageRecord


class _FakeProvider:
    def __init__(self, *, text: str = "AI-generated text", fail: bool = False) -> None:
        self._text = text
        self._fail = fail

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        if self._fail:
            raise AIProviderError("fake provider failure")
        return AIGenerationResult(text=self._text, prompt_tokens=8, completion_tokens=4)


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


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
async def approval_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_approve_pending_generation(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """Marketing Manager (ai.manage + ai.review) can generate then approve.
    Approved generation should have approval_status=APPROVED and reviewed_by_user_id set."""
    _patch_provider(monkeypatch, _FakeProvider(text="Approve this copy!"))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as client:
            # 1. Generate content
            gen_resp = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "launch email"}
            )
            assert gen_resp.status_code == 200, gen_resp.text
            gen_id = gen_resp.json()["id"]
            assert gen_resp.json()["approval_status"] == "PENDING_APPROVAL"

            # 2. Approve it
            approve_resp = await client.post(
                f"/ai/generations/{gen_id}/approve", json={"notes": "Looks great"}
            )
            assert approve_resp.status_code == 200, approve_resp.text
            body = approve_resp.json()
            assert body["approval_status"] == "APPROVED"
            assert body["review_notes"] == "Looks great"
            assert body["reviewed_at"] is not None

        # 3. DB check
        async with async_session_factory() as session:
            gen = await session.get(AIGeneration, uuid.UUID(gen_id))
        assert gen is not None
        assert gen.approval_status == "APPROVED"
        assert gen.reviewed_by_user_id == manager_id
        assert gen.review_notes == "Looks great"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_reject_pending_generation(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """Rejecting a generation sets approval_status=REJECTED and keeps the row for audit."""
    _patch_provider(monkeypatch, _FakeProvider(text="Off-brand text"))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as client:
            gen_resp = await client.post(
                "/ai/generate/SOCIAL_CAPTION", json={"brief": "product launch"}
            )
            assert gen_resp.status_code == 200
            gen_id = gen_resp.json()["id"]

            reject_resp = await client.post(
                f"/ai/generations/{gen_id}/reject", json={"notes": "Off-brand tone"}
            )
            assert reject_resp.status_code == 200, reject_resp.text
            body = reject_resp.json()
            assert body["approval_status"] == "REJECTED"
            assert body["review_notes"] == "Off-brand tone"

        async with async_session_factory() as session:
            gen = await session.get(AIGeneration, uuid.UUID(gen_id))
        assert gen is not None
        assert gen.approval_status == "REJECTED"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_edit_pending_generation(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """Editing a generation sets edited_output, preserves original output, sets
    approval_status=EDITED."""
    _patch_provider(monkeypatch, _FakeProvider(text="Original AI text"))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as client:
            gen_resp = await client.post(
                "/ai/generate/BODY_COPY", json={"brief": "welcome email"}
            )
            assert gen_resp.status_code == 200
            gen_id = gen_resp.json()["id"]

            edit_resp = await client.post(
                f"/ai/generations/{gen_id}/edit",
                json={"edited_text": "Polished human text", "notes": "Improved clarity"},
            )
            assert edit_resp.status_code == 200, edit_resp.text
            body = edit_resp.json()
            assert body["approval_status"] == "EDITED"
            assert body["edited_output"] == {"text": "Polished human text"}
            # Original output preserved
            assert body["output"] == {"text": "Original AI text"}

        async with async_session_factory() as session:
            gen = await session.get(AIGeneration, uuid.UUID(gen_id))
        assert gen is not None
        assert gen.approval_status == "EDITED"
        assert gen.edited_output == {"text": "Polished human text"}
        assert gen.output == {"text": "Original AI text"}
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approve_already_reviewed_returns_409(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """Approving an already-approved generation returns 409 (idempotency guard)."""
    _patch_provider(monkeypatch, _FakeProvider(text="Good copy"))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as client:
            gen_resp = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "sale email"}
            )
            assert gen_resp.status_code == 200
            gen_id = gen_resp.json()["id"]

            # First approval — should succeed
            r1 = await client.post(f"/ai/generations/{gen_id}/approve", json={})
            assert r1.status_code == 200

            # Second approval — should 409
            r2 = await client.post(f"/ai/generations/{gen_id}/approve", json={})
            assert r2.status_code == 409
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_content_creator_cannot_approve(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """Content Creator holds ai.manage but NOT ai.review.
    They should receive 403 when trying to approve a generation (GRX-AI-006 human gate)."""
    _patch_provider(monkeypatch, _FakeProvider(text="Created content"))
    creator_id = await user_factory(
        full_name="Content Creator", role_name="Content Creator", account_id=approval_account_id
    )
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        # Manager generates content so there's something to approve
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as manager_client:
            gen_resp = await manager_client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "sale email"}
            )
            assert gen_resp.status_code == 200
            gen_id = gen_resp.json()["id"]

        # Content Creator tries to approve — must 403
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(creator_id),
        ) as creator_client:
            approve_resp = await creator_client.post(
                f"/ai/generations/{gen_id}/approve", json={}
            )
            assert approve_resp.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approve_nonexistent_generation_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """Approving a generation that doesn't exist returns 404."""
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies=_access_token_cookie(manager_id),
    ) as client:
        resp = await client.post(f"/ai/generations/{uuid.uuid4()}/approve", json={})
        assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_generations_filter_by_approval_status(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    approval_account_id: uuid.UUID,
) -> None:
    """?approval_status=PENDING_APPROVAL returns only pending items.
    Verifies the approval queue filter works end-to-end."""
    _patch_provider(monkeypatch, _FakeProvider(text="Filtered content"))
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=approval_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as client:
            # Generate two items
            r1 = await client.post("/ai/generate/SUBJECT_LINE", json={"brief": "item 1"})
            r2 = await client.post("/ai/generate/SUBJECT_LINE", json={"brief": "item 2"})
            assert r1.status_code == 200
            assert r2.status_code == 200
            gen1_id = r1.json()["id"]

            # Approve the first one
            ar = await client.post(f"/ai/generations/{gen1_id}/approve", json={})
            assert ar.status_code == 200

            # List only PENDING_APPROVAL
            list_resp = await client.get("/ai/generations?approval_status=PENDING_APPROVAL")
            assert list_resp.status_code == 200
            items = list_resp.json()
            assert all(i["approval_status"] == "PENDING_APPROVAL" for i in items)
            ids = {i["id"] for i in items}
            assert gen1_id not in ids  # approved one excluded

            # List only APPROVED
            approved_resp = await client.get("/ai/generations?approval_status=APPROVED")
            assert approved_resp.status_code == 200
            approved_items = approved_resp.json()
            assert all(i["approval_status"] == "APPROVED" for i in approved_items)
            assert gen1_id in {i["id"] for i in approved_items}
    finally:
        await _cleanup()
