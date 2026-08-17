from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from growixa_api import health as health_module
from growixa_api.app import create_app
from growixa_api.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _test_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def _ok(_settings: Settings) -> str:
    return "ok"


async def _failing(_settings: Settings) -> str:
    return "error: connection refused"


@pytest.mark.asyncio
async def test_health_returns_ok_when_all_dependencies_are_reachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_module, "_check_postgres", _ok)
    monkeypatch.setattr(health_module, "_check_redis", _ok)
    monkeypatch.setattr(health_module, "_check_rabbitmq", _ok)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"postgres": "ok", "redis": "ok", "rabbitmq": "ok"},
    }


@pytest.mark.asyncio
async def test_health_returns_degraded_when_a_dependency_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_module, "_check_postgres", _failing)
    monkeypatch.setattr(health_module, "_check_redis", _ok)
    monkeypatch.setattr(health_module, "_check_rabbitmq", _ok)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"] == {
        "postgres": "error: connection refused",
        "redis": "ok",
        "rabbitmq": "ok",
    }
