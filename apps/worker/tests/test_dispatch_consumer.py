"""Dispatch consumer tests (GRX-SCHED-003/004): idempotency short-circuit, retry-queue
routing on failure, and DLQ + campaign FAILED after exhausting retries.

Integration-tier for the DB-touching assertions (a real campaign row, per this suite's
established real-Postgres convention — see AGENT_HANDOFF.md's GRX-TEST-001 entry). RabbitMQ
and Redis are stood in for with a fake channel/client that just records what would have been
published/stored, since what's under test here is consumer.py's *routing decisions*, not
aio_pika's or redis-py's own wire behavior (already exercised by test_jobs.py/test_redis.py).
"""

import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker import consumer as consumer_module
from growixa_worker.config import get_settings
from growixa_worker.consumer import (
    DISPATCH_DLQ,
    MAX_DISPATCH_ATTEMPTS,
    JobEnvelope,
    make_dispatch_handler,
)
from growixa_worker.db import get_session_factory
from growixa_worker.models import Campaign, EmailProviderConnection, SenderIdentity


class FakeMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def process(self) -> "FakeMessage":
        return self

    async def __aenter__(self) -> "FakeMessage":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value


class FakeDefaultExchange:
    def __init__(self, sink: list[tuple[str, dict[str, Any]]]) -> None:
        self._sink = sink

    async def publish(self, message: Any, *, routing_key: str) -> None:
        self._sink.append((routing_key, json.loads(message.body)))


class FakeChannel:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []
        self.default_exchange = FakeDefaultExchange(self.published)


def _encrypt(plaintext: str) -> str:
    return Fernet(get_settings().encryption_key.encode()).encrypt(plaintext.encode()).decode()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


async def _create_dispatching_campaign(session: AsyncSession) -> uuid.UUID:
    connection = EmailProviderConnection(
        id=uuid.uuid4(),
        provider="POSTMARK",
        smtp_host="smtp.postmarkapp.com",
        smtp_port=587,
        smtp_username="token",
        smtp_password_encrypted=_encrypt("fake-smtp-password"),
    )
    session.add(connection)
    await session.flush()
    identity = SenderIdentity(
        id=uuid.uuid4(),
        email_provider_connection_id=connection.id,
        from_email="hello@growixa.local",
        from_name="Growixa",
    )
    session.add(identity)
    await session.flush()
    campaign = Campaign(
        id=uuid.uuid4(),
        name="Dispatch consumer test",
        subject="Hi",
        body_html="<p>hi</p>",
        sender_identity_id=identity.id,
        recipient_type="ALL_CONTACTS",
        status="DISPATCHING",
    )
    session.add(campaign)
    await session.commit()
    return campaign.id


async def _cleanup(session: AsyncSession, campaign_id: uuid.UUID) -> None:
    campaign = await session.get(Campaign, campaign_id)
    if campaign is not None:
        await session.delete(campaign)
        await session.commit()
    await session.execute(delete(SenderIdentity))
    await session.execute(delete(EmailProviderConnection))
    await session.commit()


def _message_for(campaign_id: uuid.UUID, *, attempt_count: int = 0) -> Any:
    envelope = JobEnvelope(
        idempotency_key=str(uuid.uuid4()),
        job_type=consumer_module.DISPATCH_QUEUE,
        payload={"campaign_id": str(campaign_id)},
        attempt_count=attempt_count,
    )
    return FakeMessage(envelope.model_dump_json().encode()), envelope


@pytest.mark.integration
async def test_dispatch_handler_skips_when_idempotency_key_already_marked_done(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    call_count = 0

    async def _fake_handle_send_campaign(*args: object, **kwargs: object) -> None:
        nonlocal call_count
        call_count += 1

    monkeypatch.setattr(consumer_module, "handle_send_campaign", _fake_handle_send_campaign)

    campaign_id = await _create_dispatching_campaign(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(campaign_id)
        redis.store[f"grx:campaigns:dispatch:done:{envelope.idempotency_key}"] = "1"

        handler = make_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert call_count == 0
        assert channel.published == []
    finally:
        await _cleanup(session, campaign_id)


@pytest.mark.integration
async def test_dispatch_handler_marks_idempotency_key_done_after_success(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_handle_send_campaign(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(consumer_module, "handle_send_campaign", _fake_handle_send_campaign)

    campaign_id = await _create_dispatching_campaign(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(campaign_id)

        handler = make_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert redis.store[f"grx:campaigns:dispatch:done:{envelope.idempotency_key}"] == "1"
        assert channel.published == []
    finally:
        await _cleanup(session, campaign_id)


@pytest.mark.integration
async def test_dispatch_handler_routes_a_transient_failure_to_the_next_retry_queue(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raising_handle_send_campaign(*args: object, **kwargs: object) -> None:
        raise RuntimeError("transient DB blip")

    monkeypatch.setattr(consumer_module, "handle_send_campaign", _raising_handle_send_campaign)

    campaign_id = await _create_dispatching_campaign(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(campaign_id, attempt_count=0)

        handler = make_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert len(channel.published) == 1
        routing_key, body = channel.published[0]
        assert routing_key == f"{consumer_module.DISPATCH_QUEUE}.retry.0"
        assert body["attempt_count"] == 1
        assert body["idempotency_key"] == envelope.idempotency_key

        # not marked done, and the campaign itself is untouched at this point
        assert redis.store == {}
        session.expire_all()  # _mark_campaign_failed wasn't reached, but stay consistent
        campaign = await session.get(Campaign, campaign_id)
        assert campaign is not None
        assert campaign.status == "DISPATCHING"
    finally:
        await _cleanup(session, campaign_id)


@pytest.mark.integration
async def test_dispatch_handler_sends_to_dlq_and_fails_campaign_after_max_attempts(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raising_handle_send_campaign(*args: object, **kwargs: object) -> None:
        raise RuntimeError("still failing")

    monkeypatch.setattr(consumer_module, "handle_send_campaign", _raising_handle_send_campaign)

    campaign_id = await _create_dispatching_campaign(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(campaign_id, attempt_count=MAX_DISPATCH_ATTEMPTS)

        handler = make_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert len(channel.published) == 1
        routing_key, body = channel.published[0]
        assert routing_key == DISPATCH_DLQ
        assert body["idempotency_key"] == envelope.idempotency_key

        # _mark_campaign_failed committed via its own session (mirrors production, where
        # this can run after the original session's transaction has already failed) —
        # expire this session's identity map so the re-fetch below isn't served stale data.
        session.expire_all()
        campaign = await session.get(Campaign, campaign_id)
        assert campaign is not None
        assert campaign.status == "FAILED"
    finally:
        await _cleanup(session, campaign_id)
