"""Tests for the GRX-SCHED-002 campaign scheduler ticker (claim + enqueue), distinct from
the other session's mock-based test_campaigns_scheduler.py (which covers the
schedule_campaign/cancel_campaign service functions, GRX-SCHED-001)."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.campaigns import scheduler as scheduler_module
from growixa_api.campaigns.models import Campaign
from growixa_api.campaigns.scheduler import (
    DISPATCH_QUEUE,
    claim_due_campaigns,
    run_scheduler_tick,
)
from growixa_api.contacts.models import ContactList  # noqa: F401  (registers FK target metadata)
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.jobs.schemas import JobEnvelope
from growixa_api.templates.models import EmailTemplate  # noqa: F401  (registers FK target metadata)


async def _create_sender_identity(account_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = EmailProviderConnection(
            account_id=account_id,
            name="Campaign Postmark",
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
        )
        session.add(connection)
        await session.flush()
        identity = SenderIdentity(
            account_id=account_id,
            email_provider_connection_id=connection.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.commit()
        return identity.id


@pytest.fixture
async def scheduler_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


@pytest.fixture
async def sender_identity_id(scheduler_account_id: uuid.UUID) -> AsyncGenerator[uuid.UUID, None]:
    yield await _create_sender_identity(scheduler_account_id)


async def _create_campaign(
    *,
    account_id: uuid.UUID,
    sender_identity_id: uuid.UUID,
    actor_id: uuid.UUID,
    status: str,
    scheduled_at: datetime | None,
) -> uuid.UUID:
    async with async_session_factory() as session:
        campaign = Campaign(
            account_id=account_id,
            name="Scheduler ticker test",
            subject="Hi",
            body_html="<p>Hi</p>",
            sender_identity_id=sender_identity_id,
            recipient_type="ALL_CONTACTS",
            status=status,
            scheduled_at=scheduled_at,
            created_by_user_id=actor_id,
        )
        session.add(campaign)
        await session.commit()
        return campaign.id


async def _cleanup(campaign_ids: list[uuid.UUID], *, sender_identity_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        for campaign_id in campaign_ids:
            campaign = await session.get(Campaign, campaign_id)
            if campaign is None:
                continue
            await session.delete(campaign)
        await session.commit()
        identity = await session.get(SenderIdentity, sender_identity_id)
        if identity is not None:
            connection_id = identity.email_provider_connection_id
            await session.delete(identity)
            await session.commit()
            connection = await session.get(EmailProviderConnection, connection_id)
            if connection is not None:
                await session.delete(connection)
                await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_claim_due_campaigns_only_claims_scheduled_and_due(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    scheduler_account_id: uuid.UUID,
    sender_identity_id: uuid.UUID,
) -> None:
    actor_id = await user_factory(
        full_name="Ticker Test", role_name="Admin", account_id=scheduler_account_id
    )
    now = datetime.now(UTC)

    due_id = await _create_campaign(
        account_id=scheduler_account_id,
        sender_identity_id=sender_identity_id,
        actor_id=actor_id,
        status="SCHEDULED",
        scheduled_at=now,
    )
    future_id = await _create_campaign(
        account_id=scheduler_account_id,
        sender_identity_id=sender_identity_id,
        actor_id=actor_id,
        status="SCHEDULED",
        scheduled_at=now + timedelta(hours=1),
    )
    draft_id = await _create_campaign(
        account_id=scheduler_account_id,
        sender_identity_id=sender_identity_id,
        actor_id=actor_id,
        status="DRAFT",
        scheduled_at=None,
    )

    try:
        async with async_session_factory() as session:
            claimed = await claim_due_campaigns(session)
            await session.commit()

        claimed_ids = {c.id for c in claimed}
        assert due_id in claimed_ids
        assert future_id not in claimed_ids
        assert draft_id not in claimed_ids

        async with async_session_factory() as session:
            refreshed = await session.get(Campaign, due_id)
            assert refreshed is not None
            assert refreshed.status == "DISPATCHING"

            still_scheduled = await session.get(Campaign, future_id)
            assert still_scheduled is not None
            assert still_scheduled.status == "SCHEDULED"
    finally:
        await _cleanup([due_id, future_id, draft_id], sender_identity_id=sender_identity_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_scheduler_tick_publishes_one_job_per_claimed_campaign(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    scheduler_account_id: uuid.UUID,
    sender_identity_id: uuid.UUID,
) -> None:
    published: list[tuple[str, JobEnvelope]] = []

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        published.append((queue_name, envelope))

    monkeypatch.setattr(scheduler_module, "publish_job", _fake_publish_job)

    actor_id = await user_factory(
        full_name="Ticker Test 2", role_name="Admin", account_id=scheduler_account_id
    )
    due_id = await _create_campaign(
        account_id=scheduler_account_id,
        sender_identity_id=sender_identity_id,
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
        assert envelope.payload == {"campaign_id": str(due_id)}

        async with async_session_factory() as session:
            campaign = await session.get(Campaign, due_id)
            assert campaign is not None
            assert envelope.idempotency_key == str(campaign.idempotency_key)
    finally:
        await _cleanup([due_id], sender_identity_id=sender_identity_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_scheduler_tick_is_a_noop_when_nothing_is_due(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    scheduler_account_id: uuid.UUID,
    sender_identity_id: uuid.UUID,
) -> None:
    published = False

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        nonlocal published
        published = True

    monkeypatch.setattr(scheduler_module, "publish_job", _fake_publish_job)

    actor_id = await user_factory(
        full_name="Ticker Test 3", role_name="Admin", account_id=scheduler_account_id
    )
    future_id = await _create_campaign(
        account_id=scheduler_account_id,
        sender_identity_id=sender_identity_id,
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
        await _cleanup([future_id], sender_identity_id=sender_identity_id)
