import asyncio
import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage, AbstractQueue
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from growixa_worker.db import get_session_factory
from growixa_worker.models import Campaign
from growixa_worker.send_campaign import handle_send_campaign

logger = logging.getLogger("growixa_worker")

# Mirrors growixa_api.jobs.schemas.SYSTEM_HEALTHCHECK_QUEUE — the two apps share a wire
# contract (queue name + JSON envelope shape), not code, since they're separately deployed.
SYSTEM_HEALTHCHECK_QUEUE = "grx.system.healthcheck"

# Mirrors growixa_api.email_delivery.services.SEND_CAMPAIGN_QUEUE.
SEND_CAMPAIGN_QUEUE = "grx.email_delivery.send_campaign"

# Mirrors growixa_api.campaigns.scheduler.DISPATCH_QUEUE — the scheduled-campaign dispatch
# path (GRX-SCHED-002/003), kept distinct from SEND_CAMPAIGN_QUEUE's immediate "Send now"
# path so it can carry its own retry/DLQ policy without changing that path's behavior.
DISPATCH_QUEUE = "grx.campaigns.dispatch"
DISPATCH_DLQ = "grx.campaigns.dlq"

# RabbitMQ TTL + dead-letter-exchange delay pattern (no delay plugin required): each wait
# queue holds a message for its TTL with no consumer attached, then RabbitMQ dead-letters
# it back into DISPATCH_QUEUE once the TTL expires, so it's redelivered to the same handler.
_RETRY_DELAYS_MS = [60_000, 300_000, 900_000]  # 1m, 5m, 15m
MAX_DISPATCH_ATTEMPTS = len(_RETRY_DELAYS_MS)

# TTL for the Redis idempotency marker set after a dispatch job succeeds — long enough to
# outlast any plausible worker-restart redelivery window, short enough not to accumulate
# forever.
_DISPATCH_DONE_TTL_SECONDS = 24 * 60 * 60


def _retry_queue_name(attempt_index: int) -> str:
    return f"{DISPATCH_QUEUE}.retry.{attempt_index}"


class JobEnvelope(BaseModel):
    """Mirrors growixa_api.jobs.schemas.JobEnvelope — the two apps share a wire contract
    (JSON shape), not code, since they're separately deployed."""

    job_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    idempotency_key: str
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    attempt_count: int = 0
    created_by_user_id: uuid.UUID | None = None


async def parse_job_message(message: AbstractIncomingMessage) -> dict[str, Any]:
    async with message.process():
        body: dict[str, Any] = json.loads(message.body)
        return body


def make_healthcheck_handler() -> Callable[[AbstractIncomingMessage], Awaitable[None]]:
    async def handle(message: AbstractIncomingMessage) -> None:
        body = await parse_job_message(message)
        logger.info("Processed healthcheck job %s", body.get("job_id"))

    return handle


def make_send_campaign_handler() -> Callable[[AbstractIncomingMessage], Awaitable[None]]:
    async def handle(message: AbstractIncomingMessage) -> None:
        body = await parse_job_message(message)
        session_factory = get_session_factory()
        async with session_factory() as session:
            await handle_send_campaign(session, body["payload"])

    return handle


async def _publish(channel: AbstractChannel, queue_name: str, envelope: JobEnvelope) -> None:
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=envelope.model_dump_json().encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue_name,
    )


async def _mark_campaign_failed(campaign_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        campaign = await session.get(Campaign, campaign_id)
        if campaign is not None and campaign.status not in ("SENT", "FAILED"):
            campaign.status = "FAILED"
            await session.commit()


async def _route_dispatch_failure(channel: AbstractChannel, envelope: JobEnvelope) -> None:
    campaign_id_str = envelope.payload.get("campaign_id")

    if envelope.attempt_count < MAX_DISPATCH_ATTEMPTS:
        retry_queue = _retry_queue_name(envelope.attempt_count)
        retry_envelope = envelope.model_copy(update={"attempt_count": envelope.attempt_count + 1})
        await _publish(channel, retry_queue, retry_envelope)
        logger.warning(
            "dispatch: campaign %s attempt %s failed, retrying via %s",
            campaign_id_str,
            envelope.attempt_count,
            retry_queue,
        )
        return

    await _publish(channel, DISPATCH_DLQ, envelope)
    if campaign_id_str is not None:
        await _mark_campaign_failed(uuid.UUID(campaign_id_str))
    logger.error(
        "dispatch: campaign %s exhausted %s attempts, sent to DLQ",
        campaign_id_str,
        MAX_DISPATCH_ATTEMPTS,
    )


def make_dispatch_handler(
    channel: AbstractChannel, redis: Redis
) -> Callable[[AbstractIncomingMessage], Awaitable[None]]:
    """Handles scheduled-campaign dispatch jobs (GRX-SCHED-002/003) by reusing
    handle_send_campaign — the same status-agnostic handler the immediate "Send now" path
    uses, since it only guards against double-processing via CampaignVersion's existence,
    never by branching on campaign.status.

    Idempotency: marks the job's idempotency_key done in Redis *after* success, not
    before attempting — a claim-before-attempt lock would incorrectly block a legitimate
    retry after a transient failure. The DB-level CampaignVersion check inside
    handle_send_campaign remains the authoritative guard either way; this is a fast-path
    optimization against redelivery duplication after a worker restart.
    """

    async def handle(message: AbstractIncomingMessage) -> None:
        body = await parse_job_message(message)
        envelope = JobEnvelope.model_validate(body)

        done_key = f"grx:campaigns:dispatch:done:{envelope.idempotency_key}"
        if await redis.exists(done_key):
            logger.info(
                "dispatch: idempotency_key %s already processed, skipping",
                envelope.idempotency_key,
            )
            return

        session_factory = get_session_factory()
        try:
            async with session_factory() as session:
                await handle_send_campaign(session, envelope.payload)
        except Exception:
            logger.exception(
                "dispatch: campaign %s attempt %s raised",
                envelope.payload.get("campaign_id"),
                envelope.attempt_count,
            )
            await _route_dispatch_failure(channel, envelope)
            return

        await redis.set(done_key, "1", ex=_DISPATCH_DONE_TTL_SECONDS)

    return handle


async def _declare_dispatch_topology(channel: AbstractChannel) -> AbstractQueue:
    dispatch_queue = await channel.declare_queue(DISPATCH_QUEUE, durable=True)
    await channel.declare_queue(DISPATCH_DLQ, durable=True)
    for attempt_index, delay_ms in enumerate(_RETRY_DELAYS_MS):
        await channel.declare_queue(
            _retry_queue_name(attempt_index),
            durable=True,
            arguments={
                "x-message-ttl": delay_ms,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": DISPATCH_QUEUE,
            },
        )
    return dispatch_queue


async def consume_forever(rabbitmq_url: str, redis: Redis) -> None:
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        healthcheck_queue = await channel.declare_queue(SYSTEM_HEALTHCHECK_QUEUE, durable=True)
        await healthcheck_queue.consume(make_healthcheck_handler())

        send_campaign_queue = await channel.declare_queue(SEND_CAMPAIGN_QUEUE, durable=True)
        await send_campaign_queue.consume(make_send_campaign_handler())

        dispatch_queue = await _declare_dispatch_topology(channel)
        await dispatch_queue.consume(make_dispatch_handler(channel, redis))

        logger.info(
            "growixa-worker listening on %s, %s, %s",
            SYSTEM_HEALTHCHECK_QUEUE,
            SEND_CAMPAIGN_QUEUE,
            DISPATCH_QUEUE,
        )
        await asyncio.Future()
