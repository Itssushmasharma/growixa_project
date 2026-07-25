"""Shared test fixtures/factories (GRX-TEST-001).

Kept intentionally simple: each factory-created row is committed and cleaned up on its own
connection (matching the pattern already used across this suite), not wrapped in a
transactional-rollback session — see AGENT_HANDOFF.md's GRX-TEST-001 entry for why that
heavier pattern wasn't adopted yet.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import async_session_factory
from growixa_api.roles.models import Role
from growixa_api.users.models import User, UserRole


async def _create_user(session: AsyncSession, *, full_name: str, role_name: str | None) -> User:
    user = User(email=f"{uuid.uuid4()}@example.com", password_hash="x", full_name=full_name)
    session.add(user)
    await session.flush()
    if role_name is not None:
        role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one()
        session.add(UserRole(user_id=user.id, role_id=role.id))
    return user


@pytest.fixture
async def user_factory() -> AsyncGenerator[Callable[..., Awaitable[uuid.UUID]], None]:
    """Creates a real user (optionally assigned an existing seeded role); deletes every
    user it created when the test ends.

    If a test creates rows in another table that reference this user without an
    ON DELETE CASCADE (e.g. `audit_logs.actor_user_id`, by design — see GRX-AUDIT-001), the
    test itself must delete those rows before it returns, or this fixture's teardown will
    fail with a foreign-key violation.
    """
    created_ids: list[uuid.UUID] = []

    async def factory(*, full_name: str = "Test User", role_name: str | None = None) -> uuid.UUID:
        async with async_session_factory() as session:
            user = await _create_user(session, full_name=full_name, role_name=role_name)
            await session.commit()
            created_ids.append(user.id)
            return user.id

    yield factory

    async with async_session_factory() as session:
        for user_id in created_ids:
            await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
