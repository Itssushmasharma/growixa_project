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

from growixa_api.accounts.models import Account
from growixa_api.auth.security import hash_password
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.roles.models import Role
from growixa_api.users.models import User, UserRole

# Known plaintext for any user_factory-created user whose password wasn't overridden —
# tests that need to log in as that user (GRX-AUTH-002) use this constant directly.
DEFAULT_TEST_PASSWORD = "Test-Password-123!"


async def _create_user(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    full_name: str,
    role_name: str | None,
    password: str,
    email: str | None,
) -> User:
    user = User(
        account_id=account_id,
        email=email or f"{uuid.uuid4()}@example.com",
        password_hash=hash_password(password),
        full_name=full_name,
    )
    session.add(user)
    await session.flush()
    if role_name is not None:
        role = (await session.execute(select(Role).where(Role.name == role_name))).scalar_one()
        session.add(UserRole(account_id=account_id, user_id=user.id, role_id=role.id))
    return user


@pytest.fixture
async def account_factory() -> AsyncGenerator[Callable[..., Awaitable[uuid.UUID]], None]:
    """Creates a real account (GRX-SAAS-001); deletes every account it created when the
    test ends. Most tests don't need this directly — `user_factory` auto-creates one
    account per user unless an existing `account_id` is passed in. Use this fixture
    directly only for cross-tenant isolation tests that need two accounts sharing
    nothing."""
    created_ids: list[uuid.UUID] = []

    async def factory(*, name: str = "Test Account") -> uuid.UUID:
        async with async_session_factory() as session:
            account = Account(name=name)
            session.add(account)
            await session.flush()
            await session.commit()
            created_ids.append(account.id)
            return account.id

    yield factory

    async with async_session_factory() as session:
        for account_id in created_ids:
            await session.execute(delete(Account).where(Account.id == account_id))
        await session.commit()


@pytest.fixture
async def user_factory() -> AsyncGenerator[Callable[..., Awaitable[uuid.UUID]], None]:
    """Creates a real user (optionally assigned an existing seeded role, with a real Argon2
    hash of DEFAULT_TEST_PASSWORD unless overridden); deletes every user it created when the
    test ends, along with any account it auto-created for that user.

    Auto-creates a fresh `Account` per call unless an existing `account_id` is passed in
    (GRX-SAAS-001) — most tests don't care about account isolation and would otherwise all
    need updating to pass one explicitly. Tests that DO care about cross-tenant isolation
    should pass `account_id=` explicitly (from `account_factory`) to put two users in the
    same or different accounts on purpose.

    If a test creates rows in another table that reference this user without an
    ON DELETE CASCADE (e.g. `audit_logs.actor_user_id`, by design — see GRX-AUDIT-001), the
    test itself must delete those rows before it returns, or this fixture's teardown will
    fail with a foreign-key violation.
    """
    created_ids: list[uuid.UUID] = []
    auto_created_account_ids: list[uuid.UUID] = []

    async def factory(
        *,
        full_name: str = "Test User",
        role_name: str | None = None,
        password: str = DEFAULT_TEST_PASSWORD,
        email: str | None = None,
        account_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        async with async_session_factory() as session:
            resolved_account_id = account_id
            if resolved_account_id is None:
                account = Account(name=f"Test Account for {full_name}")
                session.add(account)
                await session.flush()
                resolved_account_id = account.id
                auto_created_account_ids.append(account.id)

            user = await _create_user(
                session,
                account_id=resolved_account_id,
                full_name=full_name,
                role_name=role_name,
                password=password,
                email=email,
            )
            await session.commit()
            created_ids.append(user.id)
            return user.id

    yield factory

    async with async_session_factory() as session:
        for user_id in created_ids:
            await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
        for account_id in auto_created_account_ids:
            await session.execute(delete(Account).where(Account.id == account_id))
        await session.commit()


@pytest.fixture
async def platform_admin_factory() -> AsyncGenerator[Callable[..., Awaitable[uuid.UUID]], None]:
    """Creates a real platform_admins row (GRX-SAAS-002) with a real Argon2 hash of
    DEFAULT_TEST_PASSWORD unless overridden; deletes every row it created when the test
    ends. No account_id -- platform admins are structurally outside the accounts/users
    hierarchy, see DEC-GRX-018."""
    created_ids: list[uuid.UUID] = []

    async def factory(
        *,
        full_name: str = "Test Platform Admin",
        role: str = "platform.admin",
        password: str = DEFAULT_TEST_PASSWORD,
        email: str | None = None,
        status: str = "ACTIVE",
    ) -> uuid.UUID:
        async with async_session_factory() as session:
            admin = PlatformAdmin(
                email=email or f"{uuid.uuid4()}@iitdeveloper.com",
                password_hash=hash_password(password),
                full_name=full_name,
                role=role,
                status=status,
            )
            session.add(admin)
            await session.commit()
            created_ids.append(admin.id)
            return admin.id

    yield factory

    async with async_session_factory() as session:
        for admin_id in created_ids:
            await session.execute(delete(PlatformAdmin).where(PlatformAdmin.id == admin_id))
        await session.commit()
