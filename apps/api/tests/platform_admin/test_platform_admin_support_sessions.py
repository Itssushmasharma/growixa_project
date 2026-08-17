"""Secure support session tests (GRX-SAAS-010 Phase E).

Integration-tier: exercises real Postgres and the real create_app() app. Covers
DEC-GRX-022's dedicated-view design: audited/time-limited session creation with a
separate write-access gate, account-scoped read data, the one gated write action
(editing a contact), and the customer-facing "is support looking at my account" banner
check.

support_sessions.platform_admin_id FKs to platform_admins.id ON DELETE RESTRICT (a
session must always be traceable to a real admin) -- so any test that creates a session
must delete it itself before returning, the same way user_factory's own docstring
requires for actor_user_id references without a CASCADE.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.company.models import CompanyProfile
from growixa_api.config import get_settings
from growixa_api.contacts.models import Contact
from growixa_api.db import async_session_factory
from growixa_api.platform_admin.models import SupportSession
from growixa_api.platform_auth.models import PlatformAdmin


def _customer_access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one()


async def _platform_login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


async def _delete_support_session(support_session_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(SupportSession).where(SupportSession.id == support_session_id))
        await session.commit()


async def _create_contact(session: AsyncSession, *, account_id: uuid.UUID, email: str) -> uuid.UUID:
    contact = Contact(account_id=account_id, email=email, first_name="Jane")
    session.add(contact)
    await session.flush()
    return contact.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_starting_a_read_session_succeeds_for_platform_support(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Support Session Account")
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Investigating a delivery issue", "ticket_number": "SUP-1"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["access_level"] == "READ"
    assert body["account_id"] == str(account_id)
    assert body["ended_at"] is None

    async with async_session_factory() as session:
        event = (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.entity_id == uuid.UUID(body["id"]),
                    AuditLog.action == "support_session.started",
                )
            )
        ).scalar_one()
        assert event.actor_user_id is None
        assert event.event_metadata["platform_admin_id"] == str(admin_id)
        assert event.event_metadata["reason"] == "Investigating a delivery issue"

    await _delete_support_session(uuid.UUID(body["id"]))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_starting_a_write_session_requires_the_write_permission(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """platform.support holds platform.support_session.create but not .write --
    DEC-GRX-022's "separate permission gate for write access"."""
    account_id = await account_factory(name="Write Gate Account")
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Fixing a typo", "ticket_number": "SUP-2", "access_level": "WRITE"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_overview_returns_company_and_contacts_scoped_to_the_session_account(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Overview Account")
    other_account_id = await account_factory(name="Other Account")

    async with async_session_factory() as session:
        session.add(CompanyProfile(account_id=account_id, name="Acme Inc."))
        await _create_contact(session, account_id=account_id, email="alice@example.com")
        await _create_contact(session, account_id=other_account_id, email="bob@example.com")
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        start_response = await client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Support ticket", "ticket_number": "SUP-3"},
        )
        session_id = start_response.json()["id"]

        overview_response = await client.get(f"/platform/support-sessions/{session_id}/overview")

    assert overview_response.status_code == 200
    body = overview_response.json()
    assert body["company"]["name"] == "Acme Inc."
    contact_emails = {contact["email"] for contact in body["contacts"]}
    assert contact_emails == {"alice@example.com"}

    await _delete_support_session(uuid.UUID(session_id))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_a_different_admin_cannot_use_someone_elses_session(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """THREAT_MODEL.md T38 -- knowledge of a session id alone must never be sufficient."""
    account_id = await account_factory(name="Ownership Account")
    owner_admin_id = await platform_admin_factory(role="platform.support")
    owner_email = await _get_platform_admin_email(owner_admin_id)
    other_admin_id = await platform_admin_factory(role="platform.support")
    other_email = await _get_platform_admin_email(other_admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as owner_client:
        await _platform_login(owner_client, owner_email)
        start_response = await owner_client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Owner's session", "ticket_number": "SUP-4"},
        )
    session_id = start_response.json()["id"]

    async with AsyncClient(transport=transport, base_url="http://test") as other_client:
        await _platform_login(other_client, other_email)
        overview_response = await other_client.get(
            f"/platform/support-sessions/{session_id}/overview"
        )

    assert overview_response.status_code == 404

    await _delete_support_session(uuid.UUID(session_id))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_an_expired_session_is_rejected(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """THREAT_MODEL.md T39 -- re-checked at call time, not only at creation."""
    account_id = await account_factory(name="Expiry Account")
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    async with async_session_factory() as session:
        support_session = SupportSession(
            account_id=account_id,
            platform_admin_id=admin_id,
            reason="Already expired",
            ticket_number="SUP-5",
            access_level="READ",
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        session.add(support_session)
        await session.commit()
        session_id = support_session.id

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get(f"/platform/support-sessions/{session_id}/overview")

    assert response.status_code == 410

    await _delete_support_session(session_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ending_a_session_early_prevents_further_use(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="End Early Account")
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        start_response = await client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Quick look", "ticket_number": "SUP-6"},
        )
        session_id = start_response.json()["id"]

        end_response = await client.post(f"/platform/support-sessions/{session_id}/end")
        assert end_response.status_code == 200
        assert end_response.json()["ended_at"] is not None

        overview_response = await client.get(f"/platform/support-sessions/{session_id}/overview")

    assert overview_response.status_code == 410

    await _delete_support_session(uuid.UUID(session_id))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_write_action_is_blocked_through_a_read_level_session(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """THREAT_MODEL.md T40 -- the session's own access_level is checked independently
    of the route's platform.support_session.write permission."""
    account_id = await account_factory(name="Read Only Write Attempt Account")

    async with async_session_factory() as session:
        contact_id = await _create_contact(session, account_id=account_id, email="carl@example.com")
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        start_response = await client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Just looking", "ticket_number": "SUP-7", "access_level": "READ"},
        )
        session_id = start_response.json()["id"]

        response = await client.patch(
            f"/platform/support-sessions/{session_id}/contacts/{contact_id}",
            json={"first_name": "Carla"},
        )

    assert response.status_code == 403

    await _delete_support_session(uuid.UUID(session_id))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_write_action_updates_contact_and_records_null_actor_metadata(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Write Action Account")

    async with async_session_factory() as session:
        contact_id = await _create_contact(session, account_id=account_id, email="dave@example.com")
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        start_response = await client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={
                "reason": "Fixing contact info",
                "ticket_number": "SUP-8",
                "access_level": "WRITE",
            },
        )
        session_id = start_response.json()["id"]

        response = await client.patch(
            f"/platform/support-sessions/{session_id}/contacts/{contact_id}",
            json={"first_name": "David"},
        )

    assert response.status_code == 200
    assert response.json()["first_name"] == "David"

    async with async_session_factory() as session:
        event = (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.entity_id == contact_id, AuditLog.action == "contact.updated"
                )
            )
        ).scalar_one()
        assert event.actor_user_id is None
        assert event.event_metadata["platform_admin_id"] == str(admin_id)
        assert event.event_metadata["support_session_id"] == session_id

    await _delete_support_session(uuid.UUID(session_id))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_customer_banner_reflects_an_active_session_and_clears_after_it_ends(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Banner Account")
    customer_user_id = await user_factory(account_id=account_id, full_name="Customer User")
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    customer_cookies = _customer_access_token_cookie(customer_user_id)
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=customer_cookies
    ) as customer_client:
        before_response = await customer_client.get("/accounts/support-session-status")
        assert before_response.json()["active"] is False

    async with AsyncClient(transport=transport, base_url="http://test") as admin_client:
        await _platform_login(admin_client, admin_email)
        start_response = await admin_client.post(
            f"/platform/accounts/{account_id}/support-sessions",
            json={"reason": "Customer opened a ticket", "ticket_number": "SUP-9"},
        )
        session_id = start_response.json()["id"]

    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=customer_cookies
    ) as customer_client:
        during_response = await customer_client.get("/accounts/support-session-status")
        assert during_response.json() == {
            "active": True,
            "started_at": start_response.json()["started_at"],
            "reason": "Customer opened a ticket",
        }

    async with AsyncClient(transport=transport, base_url="http://test") as admin_client:
        await _platform_login(admin_client, admin_email)
        await admin_client.post(f"/platform/support-sessions/{session_id}/end")

    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=customer_cookies
    ) as customer_client:
        after_response = await customer_client.get("/accounts/support-session-status")
        assert after_response.json()["active"] is False

    await _delete_support_session(uuid.UUID(session_id))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_starting_a_session_on_an_unknown_account_returns_404(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(
            f"/platform/accounts/{uuid.uuid4()}/support-sessions",
            json={"reason": "Nonexistent", "ticket_number": "SUP-10"},
        )

    assert response.status_code == 404
