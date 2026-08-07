"""Self-service registration flow integration tests (GRX-SAAS-003 Phase C).

Integration-tier: exercises real Postgres, the real create_app() app, and real Argon2
hashing -- no factories reused here (registration is the one flow that creates its own
account+user from scratch, unlike every other test in this suite).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from redis.exceptions import RedisError
from sqlalchemy import delete, select

from growixa_api.accounts.models import Account, AccountVerificationToken
from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.redis import client as redis_client
from growixa_api.users.models import User, UserRole


async def _cleanup(account_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        user_ids_result = await session.execute(
            select(User.id).where(User.account_id == account_id)
        )
        user_ids = list(user_ids_result.scalars().all())
        await session.execute(delete(AuditLog).where(AuditLog.account_id == account_id))
        await session.execute(
            delete(AccountVerificationToken).where(
                AccountVerificationToken.account_id == account_id
            )
        )
        await session.execute(delete(UserRole).where(UserRole.account_id == account_id))
        for user_id in user_ids:
            await session.execute(delete(User).where(User.id == user_id))
        await session.execute(delete(Account).where(Account.id == account_id))
        await session.commit()


@pytest.fixture
async def _registered() -> AsyncGenerator[dict[str, str], None]:
    """Registers one fresh account via the real endpoint; yields the response body plus
    the plaintext password and email used. Cleans up the created account/user/token."""
    email = f"{uuid.uuid4()}@example.com"
    password = "Test-Password-123!"
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/accounts/register",
            json={
                "account_name": "Acme Inc",
                "full_name": "Ada Owner",
                "email": email,
                "password": password,
                "plan_slug": "starter",
            },
        )
    assert response.status_code == 201
    body = response.json()

    yield {"email": email, "password": password, **body}

    await _cleanup(uuid.UUID(body["account_id"]))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_then_verify_then_login_happy_path(
    _registered: dict[str, str],
) -> None:
    assert _registered["token"] is not None

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # unverified: login must fail
        blocked_login = await client.post(
            "/auth/login", json={"email": _registered["email"], "password": _registered["password"]}
        )
        assert blocked_login.status_code == 401

        verify_response = await client.post(
            "/accounts/verify-email", json={"token": _registered["token"]}
        )
        assert verify_response.status_code == 204

        login_response = await client.post(
            "/auth/login", json={"email": _registered["email"], "password": _registered["password"]}
        )
        assert login_response.status_code == 200
        assert login_response.json()["id"] == _registered["user_id"]

    async with async_session_factory() as session:
        user = await session.get(User, uuid.UUID(_registered["user_id"]))
        assert user is not None
        assert user.status == "ACTIVE"

        account = await session.get(Account, uuid.UUID(_registered["account_id"]))
        assert account is not None
        assert account.selected_plan_slug == "starter"

        events_result = await session.execute(
            select(AuditLog.action).where(
                AuditLog.account_id == uuid.UUID(_registered["account_id"])
            )
        )
        actions = set(events_result.scalars().all())
    assert "account.registered" in actions
    assert "user.email_verified" in actions


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unverified_account_cannot_authenticate(_registered: dict[str, str]) -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login", json={"email": _registered["email"], "password": _registered["password"]}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_email_registration_is_rejected(_registered: dict[str, str]) -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/accounts/register",
            json={
                "account_name": "Another Co",
                "full_name": "Someone Else",
                "email": _registered["email"],
                "password": "Different-Password-1!",
                "plan_slug": "growth",
            },
        )

    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_plan_slug_is_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/accounts/register",
            json={
                "account_name": "Acme Inc",
                "full_name": "Ada Owner",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Test-Password-123!",
                "plan_slug": "enterprise",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_and_expired_and_reused_verification_tokens_are_rejected(
    _registered: dict[str, str],
) -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        garbage_response = await client.post(
            "/accounts/verify-email", json={"token": "not-a-real-token"}
        )
        assert garbage_response.status_code == 400

        async with async_session_factory() as session:
            token_result = await session.execute(
                select(AccountVerificationToken).where(
                    AccountVerificationToken.account_id == uuid.UUID(_registered["account_id"])
                )
            )
            token_row = token_result.scalar_one()
            token_row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
            await session.commit()

        expired_response = await client.post(
            "/accounts/verify-email", json={"token": _registered["token"]}
        )
        assert expired_response.status_code == 400

        async with async_session_factory() as session:
            token_result = await session.execute(
                select(AccountVerificationToken).where(
                    AccountVerificationToken.account_id == uuid.UUID(_registered["account_id"])
                )
            )
            token_row = token_result.scalar_one()
            token_row.expires_at = datetime.now(UTC) + timedelta(hours=1)
            await session.commit()

        first_verify = await client.post(
            "/accounts/verify-email", json={"token": _registered["token"]}
        )
        assert first_verify.status_code == 204

        reused_response = await client.post(
            "/accounts/verify-email", json={"token": _registered["token"]}
        )
        assert reused_response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_exceeding_the_register_threshold_returns_429_against_real_redis() -> None:
    try:
        await redis_client.ping()
    except RedisError as exc:
        pytest.skip(f"Redis not reachable from the test runner: {exc}")

    email = f"{uuid.uuid4()}@example.com"
    max_attempts = get_settings().rate_limit_max_attempts
    created_account_ids: list[uuid.UUID] = []

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(max_attempts):
            response = await client.post(
                "/accounts/register",
                json={
                    "account_name": f"Rate Limit Co {i}",
                    "full_name": "Rate Limit Owner",
                    "email": email if i == 0 else f"{uuid.uuid4()}@example.com",
                    "password": "Test-Password-123!",
                    "plan_slug": "starter",
                },
            )
            assert response.status_code == 201
            created_account_ids.append(uuid.UUID(response.json()["account_id"]))

        limited_response = await client.post(
            "/accounts/register",
            json={
                "account_name": "One Too Many",
                "full_name": "Rate Limit Owner",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Test-Password-123!",
                "plan_slug": "starter",
            },
        )
    assert limited_response.status_code == 429

    async for key in redis_client.scan_iter(match=f"grx:ratelimit:register:{email}:*"):
        await redis_client.delete(key)

    for account_id in created_account_ids:
        await _cleanup(account_id)
