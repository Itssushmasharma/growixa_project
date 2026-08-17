"""Redis connectivity smoke test (GRX-FOUND-006).

Compose's `redis` service deliberately has no host port mapping (see
docs/11-devops/LOCAL_DEVELOPMENT.md's Redis inspection section) — it's only
reachable from other containers on the compose network, not from a host-run
test runner. This test skips (rather than fails) when it can't open a real
connection, since that's an environment fact, not a code defect; the actual
set/get behavior is verified live inside the `api` container as part of this
task's Compose verification step.
"""

import uuid

import pytest
from redis.exceptions import RedisError

from growixa_api.redis import client as redis_client


@pytest.mark.asyncio
@pytest.mark.integration
async def test_can_set_and_get_a_key_against_real_redis() -> None:
    key = f"test:{uuid.uuid4()}"
    try:
        await redis_client.set(key, "value", ex=10)
    except RedisError as exc:
        pytest.skip(f"Redis not reachable from the test runner: {exc}")

    try:
        assert await redis_client.get(key) == "value"
    finally:
        await redis_client.delete(key)
