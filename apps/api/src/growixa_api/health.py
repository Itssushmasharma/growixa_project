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
