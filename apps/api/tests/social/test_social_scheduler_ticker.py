"""Tests for the GRX-SOCIAL-007 social post scheduler ticker (claim + enqueue) — a
structural mirror of test_campaign_scheduler_ticker.py."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.db import async_session_factory
from growixa_api.jobs.schemas import JobEnvelope
from growixa_api.social import scheduler as scheduler_module
from growixa_api.social.models import SocialConnection, SocialPost
from growixa_api.social.scheduler import DISPATCH_QUEUE, claim_due_posts, run_scheduler_tick


async def _create_connection(account_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = SocialConnection(
            account_id=account_id,
            provider="INSTAGRAM_BUSINESS",
            ig_business_account_id="ig-123",
            facebook_page_id="page-123",
            access_token_encrypted=encrypt_secret("fake-page-access-token"),
        )
        session.add(connection)
        await session.commit()
        return connection.id


@pytest.fixture
async def scheduler_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


@pytest.fixture
async def social_connection_id(scheduler_account_id: uuid.UUID) -> AsyncGenerator[uuid.UUID, None]:
    yield await _create_connection(scheduler_account_id)


async def _create_post(
    *,
    account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
    actor_id: uuid.UUID,
    status: str,
    scheduled_at: datetime | None,
) -> uuid.UUID:
    async with async_session_factory() as session:
        post = SocialPost(
            account_id=account_id,
            social_connection_id=social_connection_id,
            caption="Scheduler ticker test",
            status=status,
            scheduled_at=scheduled_at,
            created_by_user_id=actor_id,
        )
        session.add(post)
        await session.commit()
        return post.id


async def _cleanup(post_ids: list[uuid.UUID], *, social_connection_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        for post_id in post_ids:
            post = await session.get(SocialPost, post_id)
            if post is None:
                continue
            await session.delete(post)
        await session.commit()
        connection = await session.get(SocialConnection, social_connection_id)
        if connection is not None:
            await session.delete(connection)
            await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_claim_due_posts_only_claims_scheduled_and_due(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    scheduler_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    actor_id = await user_factory(
        full_name="Ticker Test", role_name="Admin", account_id=scheduler_account_id
    )
    now = datetime.now(UTC)

    due_id = await _create_post(
        account_id=scheduler_account_id,
        social_connection_id=social_connection_id,
        actor_id=actor_id,
        status="SCHEDULED",
        scheduled_at=now,
    )
    future_id = await _create_post(
        account_id=scheduler_account_id,
        social_connection_id=social_connection_id,
        actor_id=actor_id,
        status="SCHEDULED",
        scheduled_at=now + timedelta(hours=1),
    )
    draft_id = await _create_post(
        account_id=scheduler_account_id,
        social_connection_id=social_connection_id,
        actor_id=actor_id,
        status="DRAFT",
        scheduled_at=None,
    )

    try:
        async with async_session_factory() as session:
            claimed = await claim_due_posts(session)
            await session.commit()

        claimed_ids = {p.id for p in claimed}
        assert due_id in claimed_ids
        assert future_id not in claimed_ids
        assert draft_id not in claimed_ids

        async with async_session_factory() as session:
            refreshed = await session.get(SocialPost, due_id)
            assert refreshed is not None
            assert refreshed.status == "DISPATCHING"

            still_scheduled = await session.get(SocialPost, future_id)
            assert still_scheduled is not None
            assert still_scheduled.status == "SCHEDULED"
    finally:
        await _cleanup([due_id, future_id, draft_id], social_connection_id=social_connection_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_scheduler_tick_publishes_one_job_per_claimed_post(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    scheduler_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    published: list[tuple[str, JobEnvelope]] = []

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        published.append((queue_name, envelope))

    monkeypatch.setattr(scheduler_module, "publish_job", _fake_publish_job)

    actor_id = await user_factory(
        full_name="Ticker Test 2", role_name="Admin", account_id=scheduler_account_id
    )
    due_id = await _create_post(
        account_id=scheduler_account_id,
        social_connection_id=social_connection_id,
        actor_id=actor_id,
        status="SCHEDULED",
        scheduled_at=datetime.now(UTC),
    )

    try:
        async with async_session_factory() as session:
            claimed_count = await run_scheduler_tick(session)

        assert claimed_count == 1
        assert len(published) == 1
        queue_name, envelope = published[0]
        assert queue_name == DISPATCH_QUEUE
        assert envelope.job_type == DISPATCH_QUEUE
        assert envelope.payload == {"social_post_id": str(due_id)}

        async with async_session_factory() as session:
            post = await session.get(SocialPost, due_id)
            assert post is not None
            assert envelope.idempotency_key == str(post.idempotency_key)
    finally:
        await _cleanup([due_id], social_connection_id=social_connection_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_scheduler_tick_is_a_noop_when_nothing_is_due(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    scheduler_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    published = False

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        nonlocal published
        published = True

    monkeypatch.setattr(scheduler_module, "publish_job", _fake_publish_job)

    actor_id = await user_factory(
        full_name="Ticker Test 3", role_name="Admin", account_id=scheduler_account_id
    )
    future_id = await _create_post(
        account_id=scheduler_account_id,
        social_connection_id=social_connection_id,
        actor_id=actor_id,
        status="SCHEDULED",
        scheduled_at=datetime.now(UTC) + timedelta(hours=1),
    )

    try:
        async with async_session_factory() as session:
            claimed_count = await run_scheduler_tick(session)

        assert claimed_count == 0
        assert published is False
    finally:
        await _cleanup([future_id], social_connection_id=social_connection_id)
