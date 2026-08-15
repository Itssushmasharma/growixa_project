import aio_pika
from fastapi import APIRouter
from sqlalchemy import text

from growixa_api.config import Settings, get_settings
from growixa_api.db import engine
from growixa_api.redis import client as redis_pool

router = APIRouter()


async def _check_postgres(_settings: Settings) -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001 - a health check must report, not raise
        return f"error: {exc}"


async def _check_redis(_settings: Settings) -> str:
    try:
        await redis_pool.ping()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - a health check must report, not raise
        return f"error: {exc}"


async def _check_rabbitmq(settings: Settings) -> str:
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=3)
        await connection.close()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - a health check must report, not raise
        return f"error: {exc}"


# The primary dispatch queues plus their retry ladder (grx.campaigns.dispatch.retry.0/1/2,
# matching apps/worker/src/growixa_worker/consumer.py's MAX_DISPATCH_ATTEMPTS=3) and DLQ --
# not exposed on the public /health check (GRX-SAAS-009: this is platform-admin-only
# operational detail, gated separately in platform_admin/api.py).
_MONITORED_QUEUE_BASE_NAMES = ("grx.campaigns.dispatch", "grx.social.dispatch")
_RETRY_ATTEMPT_COUNT = 3


def _monitored_queue_names() -> list[str]:
    names: list[str] = []
    for base in _MONITORED_QUEUE_BASE_NAMES:
        names.append(base)
        names.extend(f"{base}.retry.{i}" for i in range(_RETRY_ATTEMPT_COUNT))
        names.append(f"{base.rsplit('.', 1)[0]}.dlq")
    # De-dupe while preserving order (both base names share the same *.dlq queue name shape).
    seen: set[str] = set()
    deduped: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            deduped.append(name)
    return deduped


async def get_queue_depths(settings: Settings) -> dict[str, int | str]:
    """Message count per monitored queue, via a passive (non-creating) queue declare
    on the existing AMQP connection -- avoids adding a separate RabbitMQ Management
    HTTP API client/credentials just for a read-only depth check. A queue that
    doesn't exist yet (e.g. no campaign has ever failed, so no `.retry.0` queue was
    ever declared) reports `"not declared"` rather than an error -- that's a normal,
    healthy state, not a monitoring failure."""
    depths: dict[str, int | str] = {}
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=3)
    except Exception as exc:  # noqa: BLE001 - report per-queue, not raise
        return {name: f"error: {exc}" for name in _monitored_queue_names()}
    try:
        # A fresh channel per queue: AMQP invalidates the whole channel after a
        # failed passive declare (queue-not-found), so reusing one channel across
        # queues would break every check after the first missing queue.
        for name in _monitored_queue_names():
            try:
                channel = await connection.channel()
                queue = await channel.declare_queue(name, passive=True)
                depths[name] = queue.declaration_result.message_count or 0
                await channel.close()
            except Exception:  # noqa: BLE001 - queue not declared yet is expected, not an error
                depths[name] = "not declared"
    finally:
        await connection.close()
    return depths


@router.get("/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    checks = {
        "postgres": await _check_postgres(settings),
        "redis": await _check_redis(settings),
        "rabbitmq": await _check_rabbitmq(settings),
    }
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
