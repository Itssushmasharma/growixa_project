"""Campaign report/analytics integration tests (GRX-EMAIL-006).

Integration-tier: exercises real Postgres and the real create_app() app. Fixture rows
(sender identity, contact, campaign, recipient, delivery, event) are inserted directly via
the ORM, mirroring test_email_delivery.py's webhook/unsubscribe fixture pattern, since
setting those up isn't what this test file is verifying.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.config import get_settings
from growixa_api.contacts.models import Contact
from growixa_api.db import async_session_factory
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity

CAMPAIGN_PAYLOAD = {
    "name": "Report Check",
    "subject": "Report check",
    "body_html": "<p>hello</p>",
}


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _create_sender_identity(account_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = EmailProviderConnection(
            account_id=account_id,
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
        )
        session.add(connection)
        await session.flush()
        identity = SenderIdentity(
            account_id=account_id,
            email_provider_connection_id=connection.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.commit()
        return identity.id


async def _create_campaign(
    account_id: uuid.UUID, sender_identity_id: uuid.UUID, actor_id: uuid.UUID
) -> uuid.UUID:
    async with async_session_factory() as session:
        campaign = Campaign(
            account_id=account_id,
            name=CAMPAIGN_PAYLOAD["name"],
            subject=CAMPAIGN_PAYLOAD["subject"],
            body_html=CAMPAIGN_PAYLOAD["body_html"],
            sender_identity_id=sender_identity_id,
            recipient_type="ALL_CONTACTS",
            created_by_user_id=actor_id,
            status="SENDING",
        )
        session.add(campaign)
        await session.commit()
        return campaign.id


async def _create_recipient_with_delivery(
    campaign_id: uuid.UUID,
    account_id: uuid.UUID,
    *,
    email: str,
    recipient_status: str,
    delivery_status: str | None,
    event_types: list[str] | None = None,
) -> None:
    """`delivery_status=None` means no message_deliveries row at all (e.g. a SUPPRESSED
    recipient that was never attempted). `event_types` may repeat a type to prove events
    are counted as distinct deliveries, not raw event rows."""
    async with async_session_factory() as session:
        contact = Contact(account_id=account_id, email=email)
        session.add(contact)
        await session.flush()
        recipient = CampaignRecipient(
            account_id=account_id,
            campaign_id=campaign_id,
            contact_id=contact.id,
            email=email,
            status=recipient_status,
        )
        session.add(recipient)
        await session.flush()
        if delivery_status is not None:
            delivery = MessageDelivery(
                account_id=account_id, campaign_recipient_id=recipient.id, status=delivery_status
            )
            session.add(delivery)
            await session.flush()
            for event_type in event_types or []:
                session.add(
                    EmailEvent(
                        account_id=account_id,
                        message_delivery_id=delivery.id,
                        event_type=event_type,
                        occurred_at=datetime.now(UTC),
                    )
                )
        await session.commit()


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(EmailEvent))
        await session.execute(delete(MessageDelivery))
        await session.execute(delete(CampaignRecipient))
        await session.execute(delete(Campaign).where(Campaign.name == CAMPAIGN_PAYLOAD["name"]))
        await session.execute(delete(Contact).where(Contact.email.like("%@example.com")))
        connection_ids = (
            (
                await session.execute(
                    select(SenderIdentity.email_provider_connection_id).where(
                        SenderIdentity.from_email == "hello@growixa.local"
                    )
                )
            )
            .scalars()
            .all()
        )
        await session.execute(
            delete(SenderIdentity).where(SenderIdentity.from_email == "hello@growixa.local")
        )
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.id.in_(connection_ids))
        )
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_report_reflects_delivery_and_event_counts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=account_id
    )
    sender_identity_id = await _create_sender_identity(account_id)
    campaign_id = await _create_campaign(account_id, sender_identity_id, manager_id)
    try:
        await _create_recipient_with_delivery(
            campaign_id,
            account_id,
            email="opened-clicked@example.com",
            recipient_status="SENT",
            delivery_status="DELIVERED",
            event_types=["DELIVERED", "OPENED", "OPENED", "CLICKED"],
        )
        await _create_recipient_with_delivery(
            campaign_id,
            account_id,
            email="bounced@example.com",
            recipient_status="SENT",
            delivery_status="BOUNCED",
            event_types=["BOUNCED"],
        )
        await _create_recipient_with_delivery(
            campaign_id,
            account_id,
            email="suppressed@example.com",
            recipient_status="SUPPRESSED",
            delivery_status=None,
        )

        manager_cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=manager_cookies
        ) as client:
            response = await client.get(f"/campaigns/{campaign_id}/report")

        assert response.status_code == 200
        body = response.json()
        assert body["campaign_id"] == str(campaign_id)
        assert body["sent"] == 2
        assert body["delivered"] == 1
        assert body["bounced"] == 1
        assert body["complained"] == 0
        # Two OPENED rows on the same delivery still count as one opened delivery.
        assert body["opened"] == 1
        assert body["clicked"] == 1
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_campaigns_view_only_role_can_read_report(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=account_id
    )
    analyst_id = await user_factory(
        full_name="Test Analyst", role_name="Analyst", account_id=account_id
    )
    sender_identity_id = await _create_sender_identity(account_id)
    campaign_id = await _create_campaign(account_id, sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(analyst_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.get(f"/campaigns/{campaign_id}/report")

        assert response.status_code == 200
        assert response.json()["sent"] == 0
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_role_gets_403(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=account_id
    )
    viewer_id = await user_factory(
        full_name="Test Viewer", role_name="Viewer", account_id=account_id
    )
    sender_identity_id = await _create_sender_identity(account_id)
    campaign_id = await _create_campaign(account_id, sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(viewer_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.get(f"/campaigns/{campaign_id}/report")

        assert response.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_request_is_rejected() -> None:
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/campaigns/{unknown_id}/report")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unknown_campaign_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.get(f"/campaigns/{unknown_id}/report")

    assert response.status_code == 404
