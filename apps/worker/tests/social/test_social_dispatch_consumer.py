"""Social dispatch consumer tests (GRX-SOCIAL-007/008): idempotency short-circuit,
retry-queue routing on a transient failure, DLQ + post FAILED after exhausting retries,
and the one social-specific addition — a PermanentPublishError skips the retry ladder
entirely rather than burning every remaining attempt. A structural mirror of
test_dispatch_consumer.py, same fake channel/message/redis doubles.
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
    MAX_DISPATCH_ATTEMPTS,
    SOCIAL_DISPATCH_DLQ,
    JobEnvelope,
    make_social_dispatch_handler,
)
from growixa_worker.db import get_session_factory
from growixa_worker.instagram_client import PermanentPublishError
from growixa_worker.models import SocialConnection, SocialPost, SocialPostMedia, SocialPostVersion


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


# Same seeded account every GRX-SAAS-001 migration backfills into -- see
# test_send_campaign.py's identical constant/note.
_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _create_dispatching_post(session: AsyncSession) -> uuid.UUID:
    connection = SocialConnection(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        provider="INSTAGRAM_BUSINESS",
        ig_business_account_id="ig-123",
        facebook_page_id="page-123",
        access_token_encrypted=_encrypt("fake-page-access-token"),
    )
    session.add(connection)
    await session.flush()
    post = SocialPost(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        social_connection_id=connection.id,
        caption="Dispatch consumer test",
        status="DISPATCHING",
    )
    session.add(post)
    await session.flush()
    session.add(
        SocialPostMedia(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            social_post_id=post.id,
            media_type="IMAGE",
            storage_path="x",
            public_url="https://fake-supabase.test/test.jpg",
            position=0,
        )
    )
    await session.commit()
    return post.id


async def _cleanup(session: AsyncSession, post_id: uuid.UUID) -> None:
    await session.execute(delete(SocialPostVersion))
    post = await session.get(SocialPost, post_id)
    if post is not None:
        connection_id = post.social_connection_id
        await session.execute(delete(SocialPostMedia))
        await session.delete(post)
        await session.commit()
        connection = await session.get(SocialConnection, connection_id)
        if connection is not None:
            await session.delete(connection)
            await session.commit()


def _message_for(post_id: uuid.UUID, *, attempt_count: int = 0) -> Any:
    envelope = JobEnvelope(
        idempotency_key=str(uuid.uuid4()),
        job_type=consumer_module.SOCIAL_DISPATCH_QUEUE,
        payload={"social_post_id": str(post_id)},
        attempt_count=attempt_count,
    )
    return FakeMessage(envelope.model_dump_json().encode()), envelope


@pytest.mark.integration
async def test_dispatch_handler_skips_when_idempotency_key_already_marked_done(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    call_count = 0

    async def _fake_handle_publish_social_post(*args: object, **kwargs: object) -> None:
        nonlocal call_count
        call_count += 1

    monkeypatch.setattr(
        consumer_module, "handle_publish_social_post", _fake_handle_publish_social_post
    )

    post_id = await _create_dispatching_post(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(post_id)
        redis.store[f"grx:social:dispatch:done:{envelope.idempotency_key}"] = "1"

        handler = make_social_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert call_count == 0
        assert channel.published == []
    finally:
        await _cleanup(session, post_id)


@pytest.mark.integration
async def test_dispatch_handler_marks_idempotency_key_done_after_success(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_handle_publish_social_post(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(
        consumer_module, "handle_publish_social_post", _fake_handle_publish_social_post
    )

    post_id = await _create_dispatching_post(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(post_id)

        handler = make_social_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert redis.store[f"grx:social:dispatch:done:{envelope.idempotency_key}"] == "1"
        assert channel.published == []
    finally:
        await _cleanup(session, post_id)


@pytest.mark.integration
async def test_dispatch_handler_routes_a_transient_failure_to_the_next_retry_queue(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raising_handle_publish_social_post(*args: object, **kwargs: object) -> None:
        raise RuntimeError("transient DB blip")

    monkeypatch.setattr(
        consumer_module, "handle_publish_social_post", _raising_handle_publish_social_post
    )

    post_id = await _create_dispatching_post(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(post_id, attempt_count=0)

        handler = make_social_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert len(channel.published) == 1
        routing_key, body = channel.published[0]
        assert routing_key == f"{consumer_module.SOCIAL_DISPATCH_QUEUE}.retry.0"
        assert body["attempt_count"] == 1
        assert body["idempotency_key"] == envelope.idempotency_key

        assert redis.store == {}
        session.expire_all()
        post = await session.get(SocialPost, post_id)
        assert post is not None
        assert post.status == "DISPATCHING"
    finally:
        await _cleanup(session, post_id)


@pytest.mark.integration
async def test_dispatch_handler_sends_to_dlq_and_fails_post_after_max_attempts(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raising_handle_publish_social_post(*args: object, **kwargs: object) -> None:
        raise RuntimeError("still failing")

    monkeypatch.setattr(
        consumer_module, "handle_publish_social_post", _raising_handle_publish_social_post
    )

    post_id = await _create_dispatching_post(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(post_id, attempt_count=MAX_DISPATCH_ATTEMPTS)

        handler = make_social_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert len(channel.published) == 1
        routing_key, body = channel.published[0]
        assert routing_key == SOCIAL_DISPATCH_DLQ
        assert body["idempotency_key"] == envelope.idempotency_key

        session.expire_all()
        post = await session.get(SocialPost, post_id)
        assert post is not None
        assert post.status == "FAILED"
        assert post.last_error == "still failing"
    finally:
        await _cleanup(session, post_id)


@pytest.mark.integration
async def test_dispatch_handler_sends_a_permanent_failure_straight_to_dlq_on_first_attempt(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one social-specific addition over the campaigns dispatch handler: a dead
    token (Graph error code 190) is never worth retrying, so it skips the retry ladder
    entirely -- even on attempt_count=0, this goes straight to DLQ, not retry.0."""

    async def _raising_handle_publish_social_post(*args: object, **kwargs: object) -> None:
        raise PermanentPublishError("OAuthException: token expired")

    monkeypatch.setattr(
        consumer_module, "handle_publish_social_post", _raising_handle_publish_social_post
    )

    post_id = await _create_dispatching_post(session)
    try:
        redis = FakeRedis()
        channel = FakeChannel()
        message, envelope = _message_for(post_id, attempt_count=0)

        handler = make_social_dispatch_handler(channel, redis)  # type: ignore[arg-type]
        await handler(message)

        assert len(channel.published) == 1
        routing_key, body = channel.published[0]
        assert routing_key == SOCIAL_DISPATCH_DLQ
        assert body["idempotency_key"] == envelope.idempotency_key

        session.expire_all()
        post = await session.get(SocialPost, post_id)
        assert post is not None
        assert post.status == "FAILED"
        assert "token expired" in (post.last_error or "")
    finally:
        await _cleanup(session, post_id)
