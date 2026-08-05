import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from growixa_worker.db import get_session_factory
from growixa_worker.send_campaign import handle_send_campaign

logger = logging.getLogger("growixa_worker")

# Mirrors growixa_api.jobs.schemas.SYSTEM_HEALTHCHECK_QUEUE — the two apps share a wire
# contract (queue name + JSON envelope shape), not code, since they're separately deployed.
SYSTEM_HEALTHCHECK_QUEUE = "grx.system.healthcheck"

# Mirrors growixa_api.email_delivery.services.SEND_CAMPAIGN_QUEUE.
SEND_CAMPAIGN_QUEUE = "grx.email_delivery.send_campaign"


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


async def consume_forever(rabbitmq_url: str) -> None:
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        healthcheck_queue = await channel.declare_queue(SYSTEM_HEALTHCHECK_QUEUE, durable=True)
        await healthcheck_queue.consume(make_healthcheck_handler())

        send_campaign_queue = await channel.declare_queue(SEND_CAMPAIGN_QUEUE, durable=True)
        await send_campaign_queue.consume(make_send_campaign_handler())

        logger.info(
            "growixa-worker listening on %s, %s", SYSTEM_HEALTHCHECK_QUEUE, SEND_CAMPAIGN_QUEUE
        )
        await asyncio.Future()
