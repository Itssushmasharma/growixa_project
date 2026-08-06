"""Test-send + campaign-send integration tests (GRX-EMAIL-004, api side).

Integration-tier: exercises real Postgres and the real create_app() app. The real SMTP
transport is monkeypatched here (no live Postmark account available — see AGENT_HANDOFF.md
for the documented evidence gap); the real job publish is likewise monkeypatched, following
the exact pattern already used in test_jobs.py for GRX-FOUND-007's healthcheck endpoint.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.config import get_settings
from growixa_api.contacts.models import Contact, SuppressionEntry
from growixa_api.db import async_session_factory
from growixa_api.email_delivery import services as email_delivery_services
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery, UnsubscribeEvent
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.jobs.schemas import JobEnvelope

CAMPAIGN_PAYLOAD = {
    "name": "Spring Sale",
    "subject": "Spring is here",
    "body_html": "<p>Save 20%</p>",
    "recipient_type": "ALL_CONTACTS",
}


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _create_sender_identity() -> uuid.UUID:
    async with async_session_factory() as session:
        connection = EmailProviderConnection(
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
        )
        session.add(connection)
        await session.flush()
        identity = SenderIdentity(
            email_provider_connection_id=connection.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.commit()
        return identity.id


async def _create_campaign(sender_identity_id: uuid.UUID, actor_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        campaign = Campaign(
            name=CAMPAIGN_PAYLOAD["name"],
            subject=CAMPAIGN_PAYLOAD["subject"],
            body_html=CAMPAIGN_PAYLOAD["body_html"],
            sender_identity_id=sender_identity_id,
            recipient_type="ALL_CONTACTS",
            created_by_user_id=actor_id,
        )
        session.add(campaign)
        await session.commit()
        return campaign.id


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(Campaign))
        await session.execute(delete(SenderIdentity))
        await session.execute(delete(EmailProviderConnection))
        await session.commit()


async def _create_connection_with_webhook_creds(
    webhook_username: str = "wh-user", webhook_password: str = "wh-pass"
) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = EmailProviderConnection(
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
            webhook_username=webhook_username,
            webhook_password_encrypted=encrypt_secret(webhook_password),
        )
        session.add(connection)
        await session.flush()
        identity = SenderIdentity(
            email_provider_connection_id=connection.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.commit()
        return identity.id


async def _create_delivery_for_recipient(
    sender_identity_id: uuid.UUID,
    actor_id: uuid.UUID,
    *,
    email: str = "recipient@example.com",
    provider_message_id: str | None = "pm-123",
) -> tuple[uuid.UUID, uuid.UUID]:
    """Sets up a full send-chain (contact -> campaign -> recipient -> delivery) so webhook
    and unsubscribe handling has something real to match against. Returns
    (campaign_recipient_id, message_delivery_id)."""
    async with async_session_factory() as session:
        contact = Contact(email=email)
        session.add(contact)
        await session.flush()
        campaign = Campaign(
            name=CAMPAIGN_PAYLOAD["name"],
            subject=CAMPAIGN_PAYLOAD["subject"],
            body_html=CAMPAIGN_PAYLOAD["body_html"],
            sender_identity_id=sender_identity_id,
            recipient_type="ALL_CONTACTS",
            created_by_user_id=actor_id,
            status="SENDING",
        )
        session.add(campaign)
        await session.flush()
        recipient = CampaignRecipient(
            campaign_id=campaign.id, contact_id=contact.id, email=email, status="SENT"
        )
        session.add(recipient)
        await session.flush()
        delivery = MessageDelivery(
            campaign_recipient_id=recipient.id,
            provider_message_id=provider_message_id,
            status="SENT",
        )
        session.add(delivery)
        await session.commit()
        return recipient.id, delivery.id


async def _cleanup_delivery_fixtures() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(EmailEvent))
        await session.execute(delete(MessageDelivery))
        await session.execute(delete(UnsubscribeEvent))
        await session.execute(delete(SuppressionEntry))
        await session.execute(delete(CampaignRecipient))
        await session.execute(delete(Campaign))
        await session.execute(delete(Contact))
        await session.execute(delete(SenderIdentity))
        await session.execute(delete(EmailProviderConnection))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_trigger_send_and_campaign_flips_to_sending(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    published: list[tuple[str, JobEnvelope]] = []

    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        published.append((queue_name, envelope))

    monkeypatch.setattr(email_delivery_services, "publish_job", _fake_publish_job)

    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_sender_identity()
    campaign_id = await _create_campaign(sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(f"/campaigns/{campaign_id}/send")

        assert response.status_code == 202
        assert len(published) == 1
        queue_name, envelope = published[0]
        assert queue_name == email_delivery_services.SEND_CAMPAIGN_QUEUE
        assert envelope.payload == {"campaign_id": str(campaign_id)}
        assert envelope.created_by_user_id == manager_id
        assert response.json() == {"job_id": str(envelope.job_id)}

        async with async_session_factory() as session:
            campaign = await session.get(Campaign, campaign_id)
            assert campaign is not None
            assert campaign.status == "SENDING"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sending_twice_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    async def _fake_publish_job(queue_name: str, envelope: JobEnvelope) -> None:
        return None

    monkeypatch.setattr(email_delivery_services, "publish_job", _fake_publish_job)

    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_sender_identity()
    campaign_id = await _create_campaign(sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            first_response = await client.post(f"/campaigns/{campaign_id}/send")
            second_response = await client.post(f"/campaigns/{campaign_id}/send")

        assert first_response.status_code == 202
        assert second_response.status_code == 409
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_content_creator_can_manage_but_not_send(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """The new "permission-gated action within an otherwise-accessible resource" shape
    from SPRINT_03's acceptance criteria: Content Creator has campaigns.manage but not
    campaigns.send, so editing the draft succeeds while sending it doesn't."""
    creator_id = await user_factory(full_name="Test Creator", role_name="Content Creator")
    sender_identity_id = await _create_sender_identity()
    campaign_id = await _create_campaign(sender_identity_id, creator_id)
    try:
        cookies = _access_token_cookie(creator_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            edit_response = await client.patch(
                f"/campaigns/{campaign_id}", json={"subject": "Edited by creator"}
            )
            send_response = await client.post(f"/campaigns/{campaign_id}/send")
            test_send_response = await client.post(
                f"/campaigns/{campaign_id}/test-send", json={"to_email": "test@example.com"}
            )

        assert edit_response.status_code == 200
        assert send_response.status_code == 403
        assert test_send_response.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_view_only_role_gets_403_on_send_and_test_send(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_sender_identity()
    campaign_id = await _create_campaign(sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(analyst_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            send_response = await client.post(f"/campaigns/{campaign_id}/send")
            test_send_response = await client.post(
                f"/campaigns/{campaign_id}/test-send", json={"to_email": "test@example.com"}
            )

        assert send_response.status_code == 403
        assert test_send_response.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected() -> None:
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        send_response = await client.post(f"/campaigns/{unknown_id}/send")
        test_send_response = await client.post(
            f"/campaigns/{unknown_id}/test-send", json={"to_email": "test@example.com"}
        )

    assert send_response.status_code == 401
    assert test_send_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_and_test_send_on_unknown_campaign_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        send_response = await client.post(f"/campaigns/{unknown_id}/send")
        test_send_response = await client.post(
            f"/campaigns/{unknown_id}/test-send", json={"to_email": "test@example.com"}
        )

    assert send_response.status_code == 404
    assert test_send_response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_test_send_calls_smtp_with_the_campaigns_current_draft_content(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    sent: list[dict[str, object]] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent.append(kwargs)

    monkeypatch.setattr(email_delivery_services, "send_email", _fake_send_email)

    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_sender_identity()
    campaign_id = await _create_campaign(sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(
                f"/campaigns/{campaign_id}/test-send", json={"to_email": "reviewer@example.com"}
            )

        assert response.status_code == 204
        assert len(sent) == 1
        assert sent[0]["to_email"] == "reviewer@example.com"
        assert sent[0]["subject"] == CAMPAIGN_PAYLOAD["subject"]

        async with async_session_factory() as session:
            campaign = await session.get(Campaign, campaign_id)
            assert campaign is not None
            assert campaign.status == "DRAFT"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_test_send_smtp_failure_returns_502(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    async def _failing_send_email(**kwargs: object) -> None:
        raise EmailSendError("connection refused")

    monkeypatch.setattr(email_delivery_services, "send_email", _failing_send_email)

    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_sender_identity()
    campaign_id = await _create_campaign(sender_identity_id, manager_id)
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(
                f"/campaigns/{campaign_id}/test-send", json={"to_email": "reviewer@example.com"}
            )

        assert response.status_code == 502
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_rejects_request_with_no_credentials(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Key negative test per SPRINT_03's acceptance criteria: an unauthenticated webhook
    request is rejected before it ever touches email_events/message_deliveries."""
    actor_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_connection_with_webhook_creds()
    await _create_delivery_for_recipient(sender_identity_id, actor_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Delivery",
                    "MessageID": "pm-123",
                    "Recipient": "recipient@example.com",
                },
            )

        assert response.status_code == 401

        async with async_session_factory() as session:
            events = (await session.execute(select(EmailEvent))).scalars().all()
            assert events == []
    finally:
        await _cleanup_delivery_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_rejects_wrong_credentials(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    actor_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_connection_with_webhook_creds()
    await _create_delivery_for_recipient(sender_identity_id, actor_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Delivery",
                    "MessageID": "pm-123",
                    "Recipient": "recipient@example.com",
                },
                auth=("wrong-user", "wrong-pass"),
            )

        assert response.status_code == 401

        async with async_session_factory() as session:
            events = (await session.execute(select(EmailEvent))).scalars().all()
            assert events == []
    finally:
        await _cleanup_delivery_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_delivery_event_updates_message_delivery_and_records_event(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    actor_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_connection_with_webhook_creds()
    _, delivery_id = await _create_delivery_for_recipient(sender_identity_id, actor_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Delivery",
                    "MessageID": "pm-123",
                    "Recipient": "recipient@example.com",
                    "DeliveredAt": "2026-01-01T00:00:00Z",
                },
                auth=("wh-user", "wh-pass"),
            )

        assert response.status_code == 200

        async with async_session_factory() as session:
            delivery = await session.get(MessageDelivery, delivery_id)
            assert delivery is not None
            assert delivery.status == "DELIVERED"
            assert delivery.delivered_at is not None

            events = (await session.execute(select(EmailEvent))).scalars().all()
            assert len(events) == 1
            assert events[0].event_type == "DELIVERED"
            assert events[0].message_delivery_id == delivery_id
    finally:
        await _cleanup_delivery_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_bounce_event_auto_suppresses_recipient(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """suppression_entries.reason has supported BOUNCED/COMPLAINED since Slice 2, but
    nothing wrote them until this task wired webhook-triggered auto-suppression."""
    actor_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_connection_with_webhook_creds()
    _, delivery_id = await _create_delivery_for_recipient(
        sender_identity_id, actor_id, email="bouncy@example.com"
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Bounce",
                    "MessageID": "pm-123",
                    "Recipient": "bouncy@example.com",
                },
                auth=("wh-user", "wh-pass"),
            )

        assert response.status_code == 200

        async with async_session_factory() as session:
            delivery = await session.get(MessageDelivery, delivery_id)
            assert delivery is not None
            assert delivery.status == "BOUNCED"

            suppression = (
                await session.execute(
                    select(SuppressionEntry).where(SuppressionEntry.email == "bouncy@example.com")
                )
            ).scalar_one_or_none()
            assert suppression is not None
            assert suppression.reason == "BOUNCED"
    finally:
        await _cleanup_delivery_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_unknown_message_id_is_a_noop_returns_200(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """No live Postmark account is available to verify the exact payload shape (see
    AGENT_HANDOFF.md's documented evidence gap) — an unmatched MessageID must still be
    acknowledged with 200 rather than rejected, since Postmark expects that either way."""
    actor_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_connection_with_webhook_creds()
    await _create_delivery_for_recipient(sender_identity_id, actor_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Delivery",
                    "MessageID": "no-such-message-id",
                    "Recipient": "recipient@example.com",
                },
                auth=("wh-user", "wh-pass"),
            )

        assert response.status_code == 200

        async with async_session_factory() as session:
            events = (await session.execute(select(EmailEvent))).scalars().all()
            assert events == []
    finally:
        await _cleanup_delivery_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unsubscribe_valid_link_creates_event_and_suppresses_recipient(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    actor_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    sender_identity_id = await _create_connection_with_webhook_creds()
    recipient_id, _ = await _create_delivery_for_recipient(
        sender_identity_id, actor_id, email="unsub@example.com"
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/unsubscribe/{recipient_id}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        async with async_session_factory() as session:
            unsub_events = (await session.execute(select(UnsubscribeEvent))).scalars().all()
            assert len(unsub_events) == 1
            assert unsub_events[0].email == "unsub@example.com"

            suppression = (
                await session.execute(
                    select(SuppressionEntry).where(SuppressionEntry.email == "unsub@example.com")
                )
            ).scalar_one_or_none()
            assert suppression is not None
            assert suppression.reason == "UNSUBSCRIBED"
    finally:
        await _cleanup_delivery_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unsubscribe_unknown_id_returns_404() -> None:
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/unsubscribe/{unknown_id}")

    assert response.status_code == 404
