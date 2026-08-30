"""`GET /ai/generations` pagination tests (GRX-PERF-001).

Integration-tier: exercises real Postgres and the real create_app() app. `ai_generations`
rows are inserted directly with distinct, descending `created_at` timestamps so
`ORDER BY created_at DESC` pagination is deterministic, without needing a real/mocked AI
provider call per row.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.ai.models import AIGeneration
from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.pagination import DEFAULT_LIMIT, MAX_LIMIT


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _seed_generations(
    account_id: uuid.UUID, actor_id: uuid.UUID, count: int
) -> list[uuid.UUID]:
    base = datetime.now(UTC)
    ids = [uuid.uuid4() for _ in range(count)]
    async with async_session_factory() as session:
        for i, generation_id in enumerate(ids):
            session.add(
                AIGeneration(
                    id=generation_id,
                    account_id=account_id,
                    created_by_user_id=actor_id,
                    capability="SUBJECT_LINE",
                    prompt_template_key="subject_line.v1",
                    input_context={},
                    output={"text": "generated"},
                    provider="OPENAI",
                    model="gpt-4o-mini",
                    status="COMPLETE",
                    created_at=base - timedelta(seconds=i),
                )
            )
        await session.commit()
    return ids


async def _cleanup(*generation_ids: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AIGeneration).where(AIGeneration.id.in_(generation_ids)))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_generations_default_page_size_is_bounded(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="AI Pagination Admin", role_name="Admin", account_id=account_id
    )
    generation_ids = await _seed_generations(account_id, admin_id, DEFAULT_LIMIT + 10)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/ai/generations")

        assert response.status_code == 200
        assert len(response.json()) == DEFAULT_LIMIT
    finally:
        await _cleanup(*generation_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_generations_huge_limit_is_clamped_not_honored(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="AI Pagination Clamp Admin", role_name="Admin", account_id=account_id
    )
    generation_ids = await _seed_generations(account_id, admin_id, MAX_LIMIT + 10)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.get("/ai/generations", params={"limit": 100_000})

        assert response.status_code == 200
        assert len(response.json()) == MAX_LIMIT
    finally:
        await _cleanup(*generation_ids)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_generations_offset_skips_rows_and_respects_account_isolation(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="AI Pagination Admin A", role_name="Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="AI Pagination Admin B", role_name="Admin", account_id=account_b
    )
    ids_a = await _seed_generations(account_a, admin_a, 12)
    ids_b = await _seed_generations(account_b, admin_b, 12)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client:
            page1 = await client.get("/ai/generations", params={"limit": 5, "offset": 0})
            page2 = await client.get("/ai/generations", params={"limit": 5, "offset": 5})
            # Offset past account A's own 12 rows -- must never spill into account B's rows.
            far_page = await client.get("/ai/generations", params={"limit": 50, "offset": 5})

        assert page1.status_code == 200
        assert page2.status_code == 200
        page1_ids = {row["id"] for row in page1.json()}
        page2_ids = {row["id"] for row in page2.json()}
        assert len(page1_ids) == 5
        assert len(page2_ids) == 5
        # offset genuinely skips rows at the SQL level, not a truncation of the same page.
        assert page1_ids.isdisjoint(page2_ids)

        far_page_ids = {row["id"] for row in far_page.json()}
        assert far_page_ids.issubset({str(gid) for gid in ids_a})
        assert far_page_ids.isdisjoint({str(gid) for gid in ids_b})
    finally:
        await _cleanup(*ids_a, *ids_b)
