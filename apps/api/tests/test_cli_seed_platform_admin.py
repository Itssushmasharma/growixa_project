"""Integration tests for the one-time platform admin seed CLI (apps/api/src/growixa_api/
cli/seed_platform_admin.py). Exercises real Postgres via the real async_session_factory."""

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, select

from growixa_api.cli.seed_platform_admin import main
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin


@pytest.fixture
async def cleanup_email() -> AsyncIterator[str]:
    email = f"{uuid.uuid4()}@iitdeveloper.com"
    yield email
    async with async_session_factory() as session:
        await session.execute(delete(PlatformAdmin).where(PlatformAdmin.email == email))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_creates_a_platform_owner_when_env_vars_are_set(
    cleanup_email: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PLATFORM_ADMIN_EMAIL", cleanup_email)
    monkeypatch.setenv("PLATFORM_ADMIN_PASSWORD", "Seed-Admin-Password-1!")
    monkeypatch.setenv("PLATFORM_ADMIN_FULL_NAME", "Seeded Owner")

    exit_code = await main()

    assert exit_code == 0
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == cleanup_email)
        )
        admin = result.scalar_one()
        assert admin.role == "platform.owner"
        assert admin.full_name == "Seeded Owner"
        assert admin.status == "ACTIVE"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_is_idempotent_when_run_twice(
    cleanup_email: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PLATFORM_ADMIN_EMAIL", cleanup_email)
    monkeypatch.setenv("PLATFORM_ADMIN_PASSWORD", "Seed-Admin-Password-1!")

    first = await main()
    second = await main()

    assert first == 0
    assert second == 0
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == cleanup_email)
        )
        assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_returns_1_when_env_vars_are_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PLATFORM_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("PLATFORM_ADMIN_PASSWORD", raising=False)

    assert await main() == 1
