"""Refresh-token rotation, reuse detection, logout-all, and disable-revokes-sessions tests
(GRX-AUTH-003).

Integration-tier: exercises real Postgres and the real create_app() app.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.models import RefreshToken
from growixa_api.auth.services import revoke_all_active_sessions
from growixa_api.db import async_session_factory
from growixa_api.users.models import User


async def _get_email(user_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(select(User.email).where(User.id == user_id))
        return result.scalar_one()


async def _cleanup(user_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
        await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await session.commit()


async def _login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_rotates_token_and_revokes_the_old_one(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Rotate User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, email)
        refresh_response = await client.post("/auth/refresh")

    assert refresh_response.status_code == 200

    async with async_session_factory() as session:
        result = await session.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
        tokens = result.scalars().all()

    assert len(tokens) == 2
    revoked = [t for t in tokens if t.revoked_at is not None]
    active = [t for t in tokens if t.revoked_at is None]
    assert len(revoked) == 1
    assert len(active) == 1
    assert revoked[0].replaced_by_token_id == active[0].id

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reusing_a_rotated_refresh_token_revokes_every_session(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Reuse User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, email)
        original_refresh_cookie = client.cookies.get("refresh_token")
        assert original_refresh_cookie is not None

        first_refresh = await client.post("/auth/refresh")
        assert first_refresh.status_code == 200

        # Present the ORIGINAL (now-rotated) token again — simulates a stolen-and-replayed
        # refresh token.
        client.cookies.set("refresh_token", original_refresh_cookie)
        reuse_response = await client.post("/auth/refresh")

    assert reuse_response.status_code == 401

    async with async_session_factory() as session:
        token_result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        tokens = token_result.scalars().all()

    assert len(tokens) == 2
    assert all(t.revoked_at is not None for t in tokens)

    async with async_session_factory() as session:
        audit_result = await session.execute(
            select(AuditLog).where(
                AuditLog.actor_user_id == user_id, AuditLog.action == "session.revoked"
            )
        )
        events = audit_result.scalars().all()
    assert len(events) == 1
    assert events[0].event_metadata["reason"] == "refresh_token_reuse_detected"

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logout_all_revokes_every_session(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="LogoutAll User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    # Two separate clients simulate two devices, each with their own refresh token.
    async with AsyncClient(transport=transport, base_url="http://test") as device_a:
        await _login(device_a, email)
    async with AsyncClient(transport=transport, base_url="http://test") as device_b:
        await _login(device_b, email)
        logout_all_response = await device_b.post("/auth/logout-all")

    assert logout_all_response.status_code == 204

    async with async_session_factory() as session:
        token_result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        tokens = token_result.scalars().all()

    assert len(tokens) == 2
    assert all(t.revoked_at is not None for t in tokens)

    async with async_session_factory() as session:
        audit_result = await session.execute(
            select(AuditLog).where(
                AuditLog.actor_user_id == user_id, AuditLog.action == "session.revoked"
            )
        )
        events = audit_result.scalars().all()
    assert len(events) == 1
    assert events[0].event_metadata == {"reason": "logout_all", "count": 2}

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_disabling_account_revokes_sessions_and_blocks_refresh(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Disable User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, email)

        # Simulate what a future disable-user action must do: flip status and revoke
        # sessions. No disable-user endpoint exists yet (out of apps/api/auth/'s scope) —
        # this proves the revoke_all_active_sessions() building block it will call works.
        async with async_session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            user.status = "DISABLED"
            await revoke_all_active_sessions(session, user_id, reason="account_disabled")
            await session.commit()

        refresh_response = await client.post("/auth/refresh")

    assert refresh_response.status_code == 401

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_expired_refresh_token_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Expired Token User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, email)

        async with async_session_factory() as session:
            result = await session.execute(
                select(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            token = result.scalar_one()
            token.expires_at = datetime.now(UTC) - timedelta(days=1)
            await session.commit()

        response = await client.post("/auth/refresh")

    assert response.status_code == 401

    await _cleanup(user_id)
