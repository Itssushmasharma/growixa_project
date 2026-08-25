"""Customer dashboard overview aggregation tests (GRX-SAAS-013 dashboards pass).

Integration-tier: exercises real Postgres, the real create_app() app, and the real
Free-plan subscription every account_factory-created account gets. Prerequisite rows
(contacts, campaigns, campaign_recipients, message_deliveries, email_events) are inserted
directly via the ORM. Cleanup relies on account_factory's own teardown -- every row
created here FK-cascades on accounts.id (GRX-SAAS-001).
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.app import create_app
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.config import get_settings
from growixa_api.contacts.models import Contact
from growixa_api.db import async_session_factory
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _create_contact(session: AsyncSession, *, account_id: uuid.UUID, email: str) -> uuid.UUID:
    contact = Contact(account_id=account_id, email=email)
    session.add(contact)
    await session.flush()
    return contact.id


async def _create_sender_identity(session: AsyncSession, account_id: uuid.UUID) -> uuid.UUID:
    connection = EmailProviderConnection(
        account_id=account_id,
        name="Dashboard Postmark",
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


async def _create_sent_campaign_with_engagement(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    name: str,
    delivered_count: int,
    opened_count: int,
) -> uuid.UUID:
    """One campaign with `delivered_count` DELIVERED message_deliveries, `opened_count`
    of which also have an OPENED email_event -- mirrors the real send-pipeline shape
    closely enough to exercise the same joins the dashboard queries use."""
    sender_identity_id = await _create_sender_identity(session, account_id)
    campaign = Campaign(
        account_id=account_id,
        name=name,
        subject="Subject",
        body_html="<p>Body</p>",
        sender_identity_id=sender_identity_id,
        recipient_type="ALL_CONTACTS",
        status="SENT",
    )
    session.add(campaign)
    await session.flush()

    for i in range(delivered_count):
        contact_id = await _create_contact(
            session, account_id=account_id, email=f"{uuid.uuid4()}@example.com"
        )
        recipient = CampaignRecipient(
            account_id=account_id,
            campaign_id=campaign.id,
            contact_id=contact_id,
            email=f"recipient-{i}@example.com",
            status="SENT",
        )
        session.add(recipient)
        await session.flush()

        delivery = MessageDelivery(
            account_id=account_id, campaign_recipient_id=recipient.id, status="DELIVERED"
        )
        session.add(delivery)
        await session.flush()

        if i < opened_count:
            session.add(
                EmailEvent(
                    account_id=account_id,
                    message_delivery_id=delivery.id,
                    event_type="OPENED",
                    occurred_at=datetime.now(UTC),
                )
            )
    await session.flush()
    return campaign.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_overview_requires_authentication() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/dashboard/overview")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_overview_returns_zero_state_for_a_fresh_account(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="Fresh User")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(user_id)
    ) as client:
        response = await client.get("/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_contacts"] == 0
    assert body["active_campaigns"] == 0
    assert body["email_open_rate_pct"] is None
    assert body["email_click_rate_pct"] is None
    assert body["email_ctor_pct"] is None
    assert body["recent_campaigns"] == []
    assert body["recent_activity"] == []
    assert body["quota"]["plan_name"] == "Free"
    assert body["quota"]["contact_limit"] == 250
    assert len(body["contact_growth_6_months"]) == 6


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_overview_reflects_contacts_campaigns_and_engagement(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory(name="Dashboard Data Account")
    user_id = await user_factory(full_name="Dashboard User", account_id=account_id)

    async with async_session_factory() as session:
        await _create_contact(session, account_id=account_id, email=f"{uuid.uuid4()}@example.com")
        await _create_contact(session, account_id=account_id, email=f"{uuid.uuid4()}@example.com")
        campaign_id = await _create_sent_campaign_with_engagement(
            session,
            account_id=account_id,
            name="Engagement Campaign",
            delivered_count=4,
            opened_count=1,
        )
        await session.commit()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(user_id)
    ) as client:
        response = await client.get("/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    # 2 standalone contacts + 4 auto-created recipient contacts from the campaign helper.
    assert body["total_contacts"] == 6
    assert body["campaign_status_breakdown"]["sent"] == 1
    assert body["email_open_rate_pct"] == 25.0

    assert len(body["recent_campaigns"]) == 1
    recent = body["recent_campaigns"][0]
    assert recent["id"] == str(campaign_id)
    assert recent["sent_count"] == 4
    assert recent["open_rate_pct"] == 25.0

    assert len(body["recent_activity"]) == 1
    activity = body["recent_activity"][0]
    assert activity["event_type"] == "OPENED"
    assert activity["campaign_id"] == str(campaign_id)
    assert activity["campaign_name"] == "Engagement Campaign"
