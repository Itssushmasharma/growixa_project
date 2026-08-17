from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from growixa_api.config import get_settings

client = aioredis.from_url(get_settings().redis_url, decode_responses=True)


def get_redis_client() -> aioredis.Redis:
    return client


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    yield client
