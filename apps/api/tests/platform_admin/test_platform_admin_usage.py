"""Platform Admin usage & campaign oversight tests (GRX-SAAS-008 Phase E).

Integration-tier: exercises real Postgres and the real create_app() app. Covers the
tracker's own acceptance criteria: a platform.support/platform.admin user can see any
account's usage and pause a suspicious campaign. Prerequisite rows (sender identity,
campaigns, usage records) are inserted directly via the ORM -- setting those up isn't
what this file is verifying. No manual cleanup is needed beyond account_factory's own
teardown: every row created here (campaigns, usage_records, sender_identities,
email_provider_connections, and any audit_logs this test produces) FK-cascades on
accounts.id, per GRX-SAAS-001's account-isolation retrofit.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.campaigns.models import Campaign
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.usage.models import UsageRecord


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


async def _create_sender_identity(session: AsyncSession, account_id: uuid.UUID) -> uuid.UUID:
    connection = EmailProviderConnection(
        account_id=account_id,
        provider="POSTMARK",
        smtp_host="smtp.postmarkapp.com",
        smtp_port=587,
        smtp_username="token",
        smtp_password_encrypted="encrypted",
    )
    session.add(connection)
    await session.flush()
    identity = SenderIdentity(
        account_id=account_id,
        email_provider_connection_id=connection.id,
        from_email=f"{uuid.uuid4()}@growixa.local",
        from_name="Growixa",
    )
    session.add(identity)
    await session.flush()
    return identity.id


async def _create_campaign(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    sender_identity_id: uuid.UUID,
    name: str,
    status: str,
    scheduled_at: datetime | None = None,
) -> uuid.UUID:
    campaign = Campaign(
        account_id=account_id,
        name=name,
        subject="Subject",
        body_html="<p>Body</p>",
        sender_identity_id=sender_identity_id,
        recipient_type="ALL_CONTACTS",
        status=status,
        scheduled_at=scheduled_at,
    )
    session.add(campaign)
    await session.flush()
    return campaign.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_usage_summary_aggregates_per_account_and_operation_type(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory(name="Usage Account A")
    account_b = await account_factory(name="Usage Account B")

    async with async_session_factory() as session:
        session.add_all(
            [
                UsageRecord(
                    account_id=account_a, operation_type="email.sent", quantity=10, unit="email"
                ),
                UsageRecord(
                    account_id=account_a, operation_type="email.sent", quantity=5, unit="email"
                ),
                UsageRecord(
                    account_id=account_b, operation_type="email.sent", quantity=3, unit="email"
                ),
            ]
        )
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/usage")

    assert response.status_code == 200
    rows = {(row["account_id"], row["operation_type"]): row for row in response.json()}
    row_a = rows[(str(account_a), "email.sent")]
    assert row_a["total_quantity"] == 15.0
    assert row_a["account_name"] == "Usage Account A"
    row_b = rows[(str(account_b), "email.sent")]
    assert row_b["total_quantity"] == 3.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_campaign_oversight_lists_queued_and_failed_but_not_draft_or_sent(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Oversight Account")

    async with async_session_factory() as session:
        sender_identity_id = await _create_sender_identity(session, account_id)
        scheduled_id = await _create_campaign(
            session,
            account_id=account_id,
            sender_identity_id=sender_identity_id,
            name="Scheduled Campaign",
            status="SCHEDULED",
            scheduled_at=datetime.now(UTC) + timedelta(hours=1),
        )
        failed_id = await _create_campaign(
            session,
            account_id=account_id,
            sender_identity_id=sender_identity_id,
            name="Failed Campaign",
            status="FAILED",
        )
        await _create_campaign(
            session,
            account_id=account_id,
            sender_identity_id=sender_identity_id,
            name="Draft Campaign",
            status="DRAFT",
        )
        await _create_campaign(
            session,
            account_id=account_id,
            sender_identity_id=sender_identity_id,
            name="Sent Campaign",
            status="SENT",
        )
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/campaigns")

    assert response.status_code == 200
    ids_seen = {row["id"] for row in response.json()}
    assert str(scheduled_id) in ids_seen
    assert str(failed_id) in ids_seen
    names_seen = {row["name"] for row in response.json()}
    assert "Draft Campaign" not in names_seen
    assert "Sent Campaign" not in names_seen
    scheduled_row = next(row for row in response.json() if row["id"] == str(scheduled_id))
    assert scheduled_row["account_name"] == "Oversight Account"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_pause_transitions_scheduled_campaign_and_records_audit_metadata(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Pause Target Account")

    async with async_session_factory() as session:
        sender_identity_id = await _create_sender_identity(session, account_id)
        campaign_id = await _create_campaign(
            session,
            account_id=account_id,
            sender_identity_id=sender_identity_id,
            name="Suspicious Campaign",
            status="SCHEDULED",
            scheduled_at=datetime.now(UTC) + timedelta(hours=1),
        )
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(f"/platform/campaigns/{campaign_id}/pause")

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"

    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.entity_id == campaign_id, AuditLog.action == "campaign.paused"
            )
        )
        event = result.scalar_one()
        assert event.actor_user_id is None
        assert event.event_metadata["platform_admin_id"] == str(admin_id)
        assert event.event_metadata["platform_admin_email"] == admin_email


@pytest.mark.asyncio
@pytest.mark.integration
async def test_pause_rejects_a_campaign_that_already_sent(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Already Sent Account")

    async with async_session_factory() as session:
        sender_identity_id = await _create_sender_identity(session, account_id)
        campaign_id = await _create_campaign(
            session,
            account_id=account_id,
            sender_identity_id=sender_identity_id,
            name="Already Sent Campaign",
            status="SENT",
        )
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(f"/platform/campaigns/{campaign_id}/pause")

    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_pause_unknown_campaign_returns_404(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.post(f"/platform/campaigns/{uuid.uuid4()}/pause")

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_finance_role_is_denied_usage_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Per DEC-GRX-021, only platform.owner/platform.admin/platform.support get
    platform.usage.manage -- platform.finance (billing-facing, not support-facing)
    must 403."""
    admin_id = await platform_admin_factory(role="platform.finance")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/usage")

    assert response.status_code == 403
