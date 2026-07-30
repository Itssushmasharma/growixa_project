import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger("growixa_worker")

# Mirrors growixa_api.jobs.schemas.SYSTEM_HEALTHCHECK_QUEUE — the two apps share a wire
# contract (queue name + JSON envelope shape), not code, since they're separately deployed.
SYSTEM_HEALTHCHECK_QUEUE = "grx.system.healthcheck"


async def parse_job_message(message: AbstractIncomingMessage) -> dict[str, Any]:
    async with message.process():
        body: dict[str, Any] = json.loads(message.body)
        return body


def make_healthcheck_handler() -> Callable[[AbstractIncomingMessage], Awaitable[None]]:
    async def handle(message: AbstractIncomingMessage) -> None:
        body = await parse_job_message(message)
        logger.info("Processed healthcheck job %s", body.get("job_id"))

    return handle


async def consume_forever(rabbitmq_url: str) -> None:
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(SYSTEM_HEALTHCHECK_QUEUE, durable=True)
        await queue.consume(make_healthcheck_handler())
        logger.info("growixa-worker listening on %s", SYSTEM_HEALTHCHECK_QUEUE)
        await asyncio.Future()
