from collections.abc import Awaitable
from typing import Protocol

from redis.exceptions import RedisError

from growixa_api.config import get_settings


class RateLimitExceededError(Exception):
    """Too many attempts for this identifier within the configured window."""


class _RedisLike(Protocol):
    def incr(self, name: str) -> Awaitable[int]: ...
    def expire(self, name: str, time: int) -> Awaitable[bool]: ...


async def enforce_rate_limit(redis_client: _RedisLike, *, bucket: str, identifier: str) -> None:
    """Redis-backed fixed-window rate limit, per THREAT_MODEL.md T1/T12.

    Fails open on a Redis error: the rate limiter must not become a single point of
    failure for login/password-reset availability (an unreachable Redis degrades the
    /health check the same way, but must not also lock every user out of the system).
    """
    settings = get_settings()
    key = f"grx:ratelimit:{bucket}:{identifier}"

    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, settings.rate_limit_window_seconds)
    except RedisError:
        return

    if count > settings.rate_limit_max_attempts:
        raise RateLimitExceededError
