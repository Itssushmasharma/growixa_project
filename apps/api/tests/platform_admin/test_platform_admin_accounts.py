"""Platform Admin account/user management tests (GRX-SAAS-005 Phase E).

Integration-tier: exercises real Postgres and the real create_app() app. Covers the
tracker's own acceptance criteria directly: list/suspend/reactivate any account, and a
suspended account's users cannot log in -- including the account-status-enforcement fix
this task made to auth/services.py (DEC-GRX-020).
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.accounts.repositories import get_account_id_for_user
from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import record_event
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.users.models import User


async def _get_email(user_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(select(User.email).where(User.id == user_id))
        return result.scalar_one()


async def _get_account_id(user_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        account_id = await get_account_id_for_user(session, user_id)
        assert account_id is not None
        return account_id


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one()


async def _cleanup_audit_for_user(user_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
        await session.commit()


async def _platform_login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_admin_can_list_accounts_with_user_counts(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Acme Corp")
    await user_factory(full_name="User One", account_id=account_id)
    await user_factory(full_name="User Two", account_id=account_id)

    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/accounts")

    assert response.status_code == 200
    by_id = {row["id"]: row for row in response.json()}
    assert by_id[str(account_id)]["user_count"] == 2
    assert by_id[str(account_id)]["status"] == "ACTIVE"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_account_detail_shows_users_and_filters_activity_to_security_actions(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Detail User", role_name="Admin")
    email = await _get_email(user_id)
    account_id = await _get_account_id(user_id)

    customer_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=customer_transport, base_url="http://test") as customer_client:
        login_response = await customer_client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200

    # A non-security business event on the same account, to prove the activity view is
    # filtered rather than a raw audit_logs dump (DEC-GRX-020 point 4).
    async with async_session_factory() as session:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=user_id,
            action="contact.created",
            entity_type="contact",
            entity_id=None,
            metadata={},
        )
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    platform_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=platform_transport, base_url="http://test") as admin_client:
        await _platform_login(admin_client, admin_email)
        response = await admin_client.get(f"/platform/accounts/{account_id}")

    assert response.status_code == 200
    body = response.json()
    assert {row["id"] for row in body["users"]} == {str(user_id)}
    actions = {event["action"] for event in body["security_activity"]}
    assert "user.login" in actions
    assert "contact.created" not in actions

    await _cleanup_audit_for_user(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_suspending_account_blocks_login_and_revokes_existing_sessions(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Suspend Target", role_name="Admin")
    email = await _get_email(user_id)
    account_id = await _get_account_id(user_id)

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    customer_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=customer_transport, base_url="http://test") as customer_client:
        login_response = await customer_client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        assert customer_client.cookies.get("refresh_token") is not None

        platform_transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=platform_transport, base_url="http://test"
        ) as admin_client:
            await _platform_login(admin_client, admin_email)
            suspend_response = await admin_client.patch(
                f"/platform/accounts/{account_id}/status", json={"status": "SUSPENDED"}
            )
            assert suspend_response.status_code == 200
            assert suspend_response.json()["status"] == "SUSPENDED"

        # The refresh token issued before suspension must be rejected immediately, not
        # just at the next fresh login attempt.
        refresh_response = await customer_client.post("/auth/refresh")
        assert refresh_response.status_code == 401

        login_again_response = await customer_client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )
        assert login_again_response.status_code == 401

    # audit_logs.actor_user_id cannot reference platform_admins.id -- per DEC-GRX-020 the
    # acting admin is attributed via metadata instead.
    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.account_id == account_id, AuditLog.action == "account.suspended"
            )
        )
        event = result.scalar_one()
        assert event.actor_user_id is None
        assert event.event_metadata["platform_admin_id"] == str(admin_id)
        assert event.event_metadata["platform_admin_email"] == admin_email

    await _cleanup_audit_for_user(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_closing_account_blocks_login(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Close Target", role_name="Admin")
    email = await _get_email(user_id)
    account_id = await _get_account_id(user_id)

    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)

    platform_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=platform_transport, base_url="http://test") as admin_client:
        await _platform_login(admin_client, admin_email)
        close_response = await admin_client.patch(
            f"/platform/accounts/{account_id}/status", json={"status": "CLOSED"}
        )
        assert close_response.status_code == 200
        assert close_response.json()["status"] == "CLOSED"

    customer_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=customer_transport, base_url="http://test") as customer_client:
        login_response = await customer_client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )

    assert login_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reactivating_a_suspended_account_restores_login(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Reactivate Target", role_name="Admin")
    email = await _get_email(user_id)
    account_id = await _get_account_id(user_id)

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    platform_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=platform_transport, base_url="http://test") as admin_client:
        await _platform_login(admin_client, admin_email)
        suspend_response = await admin_client.patch(
            f"/platform/accounts/{account_id}/status", json={"status": "SUSPENDED"}
        )
        assert suspend_response.status_code == 200

        reactivate_response = await admin_client.patch(
            f"/platform/accounts/{account_id}/status", json={"status": "ACTIVE"}
        )
        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["status"] == "ACTIVE"

    customer_transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=customer_transport, base_url="http://test") as customer_client:
        login_response = await customer_client.post(
            "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
        )

    assert login_response.status_code == 200

    await _cleanup_audit_for_user(user_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unknown_account_id_returns_404(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)
    unknown_id = uuid.uuid4()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        detail_response = await client.get(f"/platform/accounts/{unknown_id}")
        status_response = await client.patch(
            f"/platform/accounts/{unknown_id}/status", json={"status": "SUSPENDED"}
        )

    assert detail_response.status_code == 404
    assert status_response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_support_role_is_denied_account_management(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Per DEC-GRX-020, only platform.owner/platform.admin get platform.accounts.manage --
    every other platform role must 403."""
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/accounts")

    assert response.status_code == 403
