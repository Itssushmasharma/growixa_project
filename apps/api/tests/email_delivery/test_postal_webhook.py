import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.contacts.models import Contact, SuppressionEntry
from growixa_api.contacts.repositories import get_suppression_by_email
from growixa_api.db import async_session_factory
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity


async def _cleanup_test_data(account_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(SuppressionEntry).where(SuppressionEntry.account_id == account_id)
        )
        await session.execute(delete(EmailEvent).where(EmailEvent.account_id == account_id))
        await session.execute(
            delete(MessageDelivery).where(MessageDelivery.account_id == account_id)
        )
        await session.execute(
            delete(CampaignRecipient).where(CampaignRecipient.account_id == account_id)
        )
        await session.execute(delete(Campaign).where(Campaign.account_id == account_id))
        await session.execute(delete(SenderIdentity).where(SenderIdentity.account_id == account_id))
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.account_id == account_id)
        )
        await session.execute(delete(Contact).where(Contact.account_id == account_id))
        await session.commit()


async def _create_test_delivery(account_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, uuid.UUID]:
    campaign_id = uuid.uuid4()
    recipient_id = uuid.uuid4()
    delivery_id = uuid.uuid4()

    async with async_session_factory() as session:
        contact = Contact(account_id=account_id, email="lead@example.com")
        session.add(contact)
        await session.flush()

        connection = EmailProviderConnection(
            account_id=account_id,
            name="Postal Dedicated",
            provider="CUSTOM_SMTP",
            smtp_host="mail.iitdeveloper.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
            created_by_user_id=user_id,
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
        await session.flush()

        campaign = Campaign(
            id=campaign_id,
            account_id=account_id,
            name="Test Campaign",
            subject="Test Subject",
            body_html="<p>Test</p>",
            sender_identity_id=identity.id,
            recipient_type="ALL_CONTACTS",
            created_by_user_id=user_id,
            status="SENDING",
        )
        session.add(campaign)
        await session.flush()

        recipient = CampaignRecipient(
            id=recipient_id,
            account_id=account_id,
            campaign_id=campaign.id,
            contact_id=contact.id,
            email="lead@example.com",
            status="SENT",
        )
        session.add(recipient)
        await session.flush()

        delivery = MessageDelivery(
            id=delivery_id,
            account_id=account_id,
            campaign_recipient_id=recipient.id,
            status="SENT",
        )
        session.add(delivery)
        await session.commit()

    return {
        "account_id": account_id,
        "campaign_id": campaign_id,
        "recipient_id": recipient_id,
        "delivery_id": delivery_id,
    }


@pytest.mark.asyncio
async def test_postal_webhook_message_delivered(account_factory: Any, user_factory: Any) -> None:
    account_id = await account_factory()
    user_id = await user_factory(account_id=account_id)
    try:
        data = await _create_test_delivery(account_id, user_id)
        d_id = str(data["delivery_id"])
        payload = {
            "event": "MessageDelivered",
            "timestamp": 1724450000.0,
            "payload": {
                "message": {
                    "id": 101,
                    "token": "postal-tok-1",
                    "to": "lead@example.com",
                    "custom_headers": {
                        "x-growixa-delivery-id": d_id,
                    },
                }
            },
        }

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/webhooks/postal", json=payload)
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}

        async with async_session_factory() as session:
            delivery = await session.get(MessageDelivery, data["delivery_id"])
            assert delivery is not None
            assert delivery.status == "DELIVERED"
            assert delivery.delivered_at is not None

            recipient = await session.get(CampaignRecipient, data["recipient_id"])
            assert recipient is not None
            assert recipient.status == "SENT"

            events = (
                (
                    await session.execute(
                        select(EmailEvent).where(
                            EmailEvent.message_delivery_id == data["delivery_id"]
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 1
            assert events[0].event_type == "DELIVERED"
    finally:
        await _cleanup_test_data(account_id)


@pytest.mark.asyncio
async def test_postal_webhook_message_opened(account_factory: Any, user_factory: Any) -> None:
    account_id = await account_factory()
    user_id = await user_factory(account_id=account_id)
    try:
        data = await _create_test_delivery(account_id, user_id)
        r_id = str(data["recipient_id"])
        payload = {
            "event": "MessageLoaded",
            "timestamp": 1724450010.0,
            "payload": {
                "message": {
                    "id": 101,
                    "to": "lead@example.com",
                    "custom_headers": {
                        "x-growixa-recipient-id": r_id,
                    },
                }
            },
        }

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/webhooks/postal", json=payload)
            assert resp.status_code == 200

        async with async_session_factory() as session:
            events = (
                (
                    await session.execute(
                        select(EmailEvent).where(
                            EmailEvent.message_delivery_id == data["delivery_id"]
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 1
            assert events[0].event_type == "OPENED"
    finally:
        await _cleanup_test_data(account_id)


@pytest.mark.asyncio
async def test_postal_webhook_message_clicked(account_factory: Any, user_factory: Any) -> None:
    account_id = await account_factory()
    user_id = await user_factory(account_id=account_id)
    try:
        data = await _create_test_delivery(account_id, user_id)
        d_id = str(data["delivery_id"])
        payload = {
            "event": "MessageClicked",
            "timestamp": 1724450020.0,
            "payload": {
                "message": {
                    "id": 101,
                    "to": "lead@example.com",
                    "custom_headers": {
                        "X-Growixa-Delivery-ID": d_id,
                    },
                },
                "url": "https://iitdeveloper.com/pricing",
            },
        }

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/webhooks/postal", json=payload)
            assert resp.status_code == 200

        async with async_session_factory() as session:
            events = (
                (
                    await session.execute(
                        select(EmailEvent).where(
                            EmailEvent.message_delivery_id == data["delivery_id"]
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 1
            assert events[0].event_type == "CLICKED"
    finally:
        await _cleanup_test_data(account_id)


@pytest.mark.asyncio
async def test_postal_webhook_message_bounced(account_factory: Any, user_factory: Any) -> None:
    account_id = await account_factory()
    user_id = await user_factory(account_id=account_id)
    try:
        data = await _create_test_delivery(account_id, user_id)
        d_id = str(data["delivery_id"])
        payload = {
            "event": "MessageBounced",
            "timestamp": 1724450030.0,
            "payload": {
                "message": {
                    "id": 101,
                    "to": "lead@example.com",
                    "custom_headers": {
                        "x-growixa-delivery-id": d_id,
                    },
                }
            },
        }

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/webhooks/postal", json=payload)
            assert resp.status_code == 200

        async with async_session_factory() as session:
            delivery = await session.get(MessageDelivery, data["delivery_id"])
            assert delivery is not None
            assert delivery.status == "BOUNCED"
            assert delivery.bounced_at is not None

            events = (
                (
                    await session.execute(
                        select(EmailEvent).where(
                            EmailEvent.message_delivery_id == data["delivery_id"]
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 1
            assert events[0].event_type == "BOUNCED"

            suppression = await get_suppression_by_email(
                session, data["account_id"], "lead@example.com"
            )
            assert suppression is not None
            assert suppression.reason == "BOUNCED"
    finally:
        await _cleanup_test_data(account_id)
