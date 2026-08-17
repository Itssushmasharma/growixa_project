"""Login/logout integration tests (GRX-AUTH-002).

Integration-tier: exercises real Postgres, the real create_app() app, and real Argon2
hashing via the shared user_factory fixture (conftest.py).
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.models import RefreshToken
from growixa_api.db import async_session_factory
from growixa_api.users.models import User
from tests.conftest import DEFAULT_TEST_PASSWORD


async def _get_email(user_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(select(User.email).where(User.id == user_id))
        return result.scalar_one()


async def _cleanup_audit_for(user_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_valid_login_issues_cookies_no_tokens_in_body_and_audit_event(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Login Admin", role_name="Admin")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )

    assert response.status_code == 200
    body = response.json()
    assert body == {"id": str(user_id), "email": email, "full_name": "Login Admin"}
    assert "access_token" not in body
    assert "refresh_token" not in body

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert len(set_cookie_headers) == 2
    for header in set_cookie_headers:
        assert "HttpOnly" in header
        assert "samesite=lax" in header.lower()

    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.actor_user_id == user_id, AuditLog.action == "user.login"
            )
        )
        events = result.scalars().all()
    assert len(events) == 1

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        assert user is not None
        assert user.last_login_at is not None

    await _cleanup_audit_for(user_id)
    async with async_session_factory() as session:
        await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_wrong_password_and_unknown_email_return_identical_generic_error(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Wrong Password User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        wrong_password_response = await client.post(
            "/auth/login", json={"email": email, "password": "not-the-password"}
        )
        unknown_email_response = await client.post(
            "/auth/login",
            json={"email": f"{uuid.uuid4()}@example.com", "password": "irrelevant"},
        )

    assert wrong_password_response.status_code == 401
    assert unknown_email_response.status_code == 401
    assert wrong_password_response.json() == unknown_email_response.json()

    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == "user.login_failed")
        )
        events = result.scalars().all()
    matching = [e for e in events if e.entity_id == user_id]
    assert len(matching) == 1

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.action == "user.login_failed"))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_disabled_account_cannot_login(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Disabled User")
    email = await _get_email(user_id)

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        assert user is not None
        user.status = "DISABLED"
        await session.commit()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )

    assert response.status_code == 401

    await _cleanup_audit_for(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logout_revokes_refresh_token_and_clears_cookies(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Logout User")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200

        logout_response = await client.post("/auth/logout")

    assert logout_response.status_code == 204
    clear_headers = logout_response.headers.get_list("set-cookie")
    assert any('access_token=""' in h or "access_token=" in h for h in clear_headers)

    async with async_session_factory() as session:
        token_result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        tokens = token_result.scalars().all()
    assert len(tokens) == 1
    assert tokens[0].revoked_at is not None

    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.actor_user_id == user_id, AuditLog.action == "user.logout"
            )
        )
        events = result.scalars().all()
    assert len(events) == 1

    await _cleanup_audit_for(user_id)
    async with async_session_factory() as session:
        await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_me_returns_the_logged_in_user_and_their_permissions(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Me Route User", role_name="Admin")
    email = await _get_email(user_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200

        me_response = await client.get("/auth/me")

    assert me_response.status_code == 200
    body = me_response.json()
    assert body["id"] == str(user_id)
    assert body["email"] == email
    assert body["full_name"] == "Me Route User"
    assert "company.settings.edit" in body["permissions"]

    await _cleanup_audit_for(user_id)
    async with async_session_factory() as session:
        await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_me_without_a_session_is_unauthorized() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401
