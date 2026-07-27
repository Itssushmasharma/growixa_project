"""Rate limiter tests (GRX-AUTH-004).

The unit tests below run against a fake in-memory Redis stand-in — no real Redis needed,
so they run identically in every environment. The one integration test at the bottom
exercises the real /auth/login endpoint against real Compose Redis and skips (rather than
failing) when that's unreachable, for the same documented reason as tests/test_redis.py:
Compose's `redis` service has no host port mapping by design.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.rate_limit import RateLimitExceededError, enforce_rate_limit
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.redis import client as redis_client
from growixa_api.users.models import User


class _FakeRedis:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    async def incr(self, name: str) -> int:
        self._counts[name] = self._counts.get(name, 0) + 1
        return self._counts[name]

    async def expire(self, name: str, time: int) -> bool:
        return True


class _BrokenRedis:
    async def incr(self, name: str) -> int:
        raise RedisConnectionError("connection refused")

    async def expire(self, name: str, time: int) -> bool:
        raise RedisConnectionError("connection refused")


@pytest.mark.asyncio
async def test_allows_attempts_up_to_the_configured_max() -> None:
    redis_client = _FakeRedis()
    identifier = f"user-{uuid.uuid4()}@example.com:127.0.0.1"
    max_attempts = get_settings().rate_limit_max_attempts

    for _ in range(max_attempts):
        await enforce_rate_limit(redis_client, bucket="test", identifier=identifier)


@pytest.mark.asyncio
async def test_raises_once_the_max_is_exceeded() -> None:
    redis_client = _FakeRedis()
    identifier = f"user-{uuid.uuid4()}@example.com:127.0.0.1"
    max_attempts = get_settings().rate_limit_max_attempts

    for _ in range(max_attempts):
        await enforce_rate_limit(redis_client, bucket="test", identifier=identifier)

    with pytest.raises(RateLimitExceededError):
        await enforce_rate_limit(redis_client, bucket="test", identifier=identifier)


@pytest.mark.asyncio
async def test_different_identifiers_are_tracked_independently() -> None:
    redis_client = _FakeRedis()
    max_attempts = get_settings().rate_limit_max_attempts
    exhausted_identifier = f"user-{uuid.uuid4()}@example.com:127.0.0.1"
    other_identifier = f"user-{uuid.uuid4()}@example.com:127.0.0.1"

    for _ in range(max_attempts):
        await enforce_rate_limit(redis_client, bucket="test", identifier=exhausted_identifier)

    # a different identifier in the same bucket must not be affected
    await enforce_rate_limit(redis_client, bucket="test", identifier=other_identifier)


@pytest.mark.asyncio
async def test_different_buckets_are_tracked_independently() -> None:
    redis_client = _FakeRedis()
    max_attempts = get_settings().rate_limit_max_attempts
    identifier = f"user-{uuid.uuid4()}@example.com:127.0.0.1"

    for _ in range(max_attempts):
        await enforce_rate_limit(redis_client, bucket="login", identifier=identifier)

    # same identifier, different bucket — login and password-reset-request are independent
    await enforce_rate_limit(redis_client, bucket="password_reset_request", identifier=identifier)


@pytest.mark.asyncio
async def test_fails_open_when_redis_is_unreachable() -> None:
    redis_client = _BrokenRedis()
    identifier = f"user-{uuid.uuid4()}@example.com:127.0.0.1"

    # far past any configured threshold — must never raise, since a Redis outage must not
    # block login/password-reset entirely
    for _ in range(get_settings().rate_limit_max_attempts * 5):
        await enforce_rate_limit(redis_client, bucket="test", identifier=identifier)


async def _get_email(user_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(select(User.email).where(User.id == user_id))
        return result.scalar_one()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_exceeding_the_login_threshold_returns_429_against_real_redis(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    try:
        await redis_client.ping()
    except RedisError as exc:
        pytest.skip(f"Redis not reachable from the test runner: {exc}")

    user_id = await user_factory(full_name="Rate Limit User")
    email = await _get_email(user_id)
    max_attempts = get_settings().rate_limit_max_attempts

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(max_attempts):
            response = await client.post(
                "/auth/login", json={"email": email, "password": "wrong-password"}
            )
            assert response.status_code == 401

        limited_response = await client.post(
            "/auth/login", json={"email": email, "password": "wrong-password"}
        )
    assert limited_response.status_code == 429

    async for key in redis_client.scan_iter(match=f"grx:ratelimit:login:{email}:*"):
        await redis_client.delete(key)

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.action == "user.login_failed"))
        await session.commit()
