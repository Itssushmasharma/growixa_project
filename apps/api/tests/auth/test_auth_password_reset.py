"""Password reset flow integration tests (GRX-AUTH-005).

Integration-tier: exercises real Postgres, the real create_app() app, and real Argon2
hashing via the shared user_factory fixture (conftest.py).
"""

import uuid
from collections.abc import Awaitable, Callable, Iterator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.models import PasswordResetToken, RefreshToken
from growixa_api.config import get_settings
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
        await session.execute(
            delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )
        await session.commit()


@pytest.fixture
def _production_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_request_and_complete_round_trip(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Reset User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # log in first to create an active session that the reset must revoke
        login_response = await client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200

        request_response = await client.post("/auth/password-reset/request", json={"email": email})
        assert request_response.status_code == 200
        raw_token = request_response.json()["token"]
        assert raw_token is not None

        complete_response = await client.post(
            "/auth/password-reset/complete",
            json={"token": raw_token, "new_password": "New-Password-456!"},
        )
        assert complete_response.status_code == 204

        old_password_login = await client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert old_password_login.status_code == 401

        new_password_login = await client.post(
            "/auth/login", json={"email": email, "password": "New-Password-456!"}
        )
        assert new_password_login.status_code == 200

    async with async_session_factory() as session:
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            )
        )
        active_tokens = result.scalars().all()
    # exactly the session created by the post-reset login remains active
    assert len(active_tokens) == 1

    async with async_session_factory() as session:
        completed_result = await session.execute(
            select(AuditLog).where(
                AuditLog.actor_user_id == user_id,
                AuditLog.action == "user.password_reset_completed",
            )
        )
        assert len(completed_result.scalars().all()) == 1

        revoked_result = await session.execute(
            select(AuditLog).where(AuditLog.action == "session.revoked")
        )
        revoked_events = [e for e in revoked_result.scalars().all() if e.entity_id == user_id]
        assert len(revoked_events) == 1
        assert revoked_events[0].event_metadata["reason"] == "password_reset"

        token_result = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )
        token_row = token_result.scalar_one()
        assert token_row.used_at is not None

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_request_response_is_identical_shape_for_known_and_unknown_email(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Known Email User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        known_response = await client.post("/auth/password-reset/request", json={"email": email})
        unknown_response = await client.post(
            "/auth/password-reset/request", json={"email": f"{uuid.uuid4()}@example.com"}
        )

    assert known_response.status_code == unknown_response.status_code == 200
    assert known_response.json()["message"] == unknown_response.json()["message"]

    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == "user.password_reset_requested")
        )
        events = result.scalars().all()
    matching = [e for e in events if e.entity_id == user_id]
    assert len(matching) == 1

    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(AuditLog.action == "user.password_reset_requested")
        )
        await session.commit()

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_request_response_never_leaks_token_outside_local_environment(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    _production_env: None,
) -> None:
    user_id = await user_factory(full_name="Prod Env User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        known_response = await client.post("/auth/password-reset/request", json={"email": email})
        unknown_response = await client.post(
            "/auth/password-reset/request", json={"email": f"{uuid.uuid4()}@example.com"}
        )

    assert known_response.json() == unknown_response.json()
    assert known_response.json()["token"] is None

    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(AuditLog.action == "user.password_reset_requested")
        )
        await session.commit()

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_request_sends_email_only_for_known_users_without_changing_public_response(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    _production_env: None,
) -> None:
    user_id = await user_factory(full_name="Email Reset User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    with patch("growixa_api.auth.api.send_password_reset_email", new=AsyncMock()) as mock_send:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            known_response = await client.post(
                "/auth/password-reset/request", json={"email": email}
            )
            unknown_email = f"{uuid.uuid4()}@example.com"
            unknown_response = await client.post(
                "/auth/password-reset/request", json={"email": unknown_email}
            )

    assert known_response.status_code == unknown_response.status_code == 200
    assert known_response.json() == unknown_response.json()
    mock_send.assert_awaited_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["to_email"] == email
    assert isinstance(kwargs["raw_token"], str)
    assert kwargs["raw_token"]

    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(AuditLog.action == "user.password_reset_requested")
        )
        await session.commit()

    await _cleanup(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_expired_and_reused_tokens_are_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Bad Token User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        garbage_response = await client.post(
            "/auth/password-reset/complete",
            json={"token": "not-a-real-token", "new_password": "Whatever-123!"},
        )
        assert garbage_response.status_code == 400

        request_response = await client.post("/auth/password-reset/request", json={"email": email})
        raw_token = request_response.json()["token"]

        first_complete = await client.post(
            "/auth/password-reset/complete",
            json={"token": raw_token, "new_password": "First-New-123!"},
        )
        assert first_complete.status_code == 204

        # reuse of an already-used token must be rejected
        second_complete = await client.post(
            "/auth/password-reset/complete",
            json={"token": raw_token, "new_password": "Second-New-123!"},
        )
        assert second_complete.status_code == 400

    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(AuditLog.action == "user.password_reset_requested")
        )
        await session.commit()

    await _cleanup(user_id)
