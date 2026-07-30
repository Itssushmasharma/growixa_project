"""Job envelope, producer, and healthcheck-trigger endpoint tests (GRX-FOUND-007).

The producer round-trip test is integration-tier: Compose's `rabbitmq` service
deliberately has no host AMQP port mapping (see compose.yaml), so it's only reachable from
other containers, not from a host-run test runner — matching the established skip pattern
from GRX-FOUND-006's Redis test. It runs for real in CI, where the service container is
host-reachable (see ci.yml).
"""

import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC

import aio_pika
import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.jobs import api as jobs_api_module
from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import SYSTEM_HEALTHCHECK_QUEUE, JobEnvelope


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


def test_job_envelope_fills_in_defaults() -> None:
    envelope = JobEnvelope(idempotency_key="key-1", job_type=SYSTEM_HEALTHCHECK_QUEUE)

    assert isinstance(envelope.job_id, uuid.UUID)
    assert envelope.payload == {}
    assert envelope.attempt_count == 0
    assert envelope.created_by_user_id is None
    assert envelope.created_at.tzinfo is UTC


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_trigger_a_healthcheck_job(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    published: list[tuple[str, JobEnvelope]] = []

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        published.append((queue_name, envelope))

    monkeypatch.setattr(jobs_api_module, "publish_job", _fake_publish_job)

    admin_id = await user_factory(full_name="Jobs Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post("/system/jobs/healthcheck")

    assert response.status_code == 202
    assert len(published) == 1
    queue_name, envelope = published[0]
    assert queue_name == SYSTEM_HEALTHCHECK_QUEUE
    assert envelope.job_type == SYSTEM_HEALTHCHECK_QUEUE
    assert envelope.created_by_user_id == admin_id
    assert response.json() == {"job_id": str(envelope.job_id)}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_admin_cannot_trigger_a_healthcheck_job(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    published = False

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        nonlocal published
        published = True

    monkeypatch.setattr(jobs_api_module, "publish_job", _fake_publish_job)

    viewer_id = await user_factory(full_name="Jobs Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.post("/system/jobs/healthcheck")

    assert response.status_code == 403
    assert published is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_publish_job_delivers_the_envelope_to_the_declared_queue() -> None:
    queue_name = f"test.jobs.{uuid.uuid4()}"
    envelope = JobEnvelope(idempotency_key="round-trip-key", job_type=queue_name)

    try:
        connection = await aio_pika.connect_robust(get_settings().rabbitmq_url, timeout=3)
    except Exception as exc:  # noqa: BLE001 - environment fact, not a code defect
        pytest.skip(f"RabbitMQ not reachable from the test runner: {exc}")

    try:
        await publish_job(queue_name, envelope)

        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        message = await queue.get(timeout=5)
        assert message is not None
        body = json.loads(message.body)
        assert body["idempotency_key"] == "round-trip-key"
        assert body["job_type"] == queue_name
        await message.ack()
        await queue.delete()
    finally:
        await connection.close()
