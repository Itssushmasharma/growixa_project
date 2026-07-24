import aio_pika
import redis.asyncio as redis_client
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from growixa_api.config import Settings, get_settings

router = APIRouter()


async def _check_postgres(settings: Settings) -> str:
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - a health check must report, not raise
        return f"error: {exc}"


async def _check_redis(settings: Settings) -> str:
    try:
        client = redis_client.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
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
