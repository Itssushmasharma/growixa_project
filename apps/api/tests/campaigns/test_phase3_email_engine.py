import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

pytestmark = pytest.mark.integration

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.config import get_settings
from growixa_api.contacts.models import Contact
from growixa_api.db import async_session_factory
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.integrations.providers import (
    BaseEmailProvider,
    CustomSmtpEmailProvider,
    PostmarkEmailProvider,
    get_email_provider,
)
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


@pytest.mark.asyncio
async def test_provider_abstraction_and_factory():
    encrypted_pw = encrypt_secret("super_secret_smtp_pw")
    postmark_conn = EmailProviderConnection(
        account_id=uuid.uuid4(),
        name="Postmark Rel",
        provider="POSTMARK",
        smtp_host="smtp.postmarkapp.com",
        smtp_port=587,
        smtp_username="pm_token",
        smtp_password_encrypted=encrypted_pw,
    )
    provider_pm = get_email_provider(postmark_conn)
    assert isinstance(provider_pm, BaseEmailProvider)
    assert isinstance(provider_pm, PostmarkEmailProvider)
    assert provider_pm.provider_name == "POSTMARK"
    assert provider_pm.password == "super_secret_smtp_pw"

    custom_conn = EmailProviderConnection(
        account_id=uuid.uuid4(),
        name="Custom Rel",
        provider="CUSTOM_SMTP",
        smtp_host="mail.example.com",
        smtp_port=465,
        smtp_username="smtp_user",
        smtp_password_encrypted=encrypted_pw,
    )
    provider_custom = get_email_provider(custom_conn)
    assert isinstance(provider_custom, BaseEmailProvider)
    assert isinstance(provider_custom, CustomSmtpEmailProvider)
    assert provider_custom.provider_name == "CUSTOM_SMTP"
    assert provider_custom.port == 465

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await provider_custom.send_email(
            from_email="noreply@example.com",
            from_name="Test Sender",
            to_email="customer@example.com",
            subject="Test Subject",
            body_html="<p>Hello</p>",
            body_text="Hello",
        )
        assert mock_send.await_count == 1
        call_kwargs = mock_send.call_args.kwargs
        assert call_kwargs["hostname"] == "mail.example.com"
        assert call_kwargs["use_tls"] is True


@pytest.mark.asyncio
async def test_template_duplication_and_validation(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
):
    account_id = await account_factory()
    admin_id = await user_factory(role_name="Admin", account_id=account_id)
    app = create_app()
    cookies = _access_token_cookie(admin_id)

    async with async_session_factory() as session:
        t = EmailTemplate(account_id=account_id, name="Original Promo")
        session.add(t)
        await session.flush()
        session.add(
            EmailTemplateVersion(
                account_id=account_id,
                template_id=t.id,
                version_number=1,
                subject="Big Sale {{first_name}}",
                body_html="<p>Click <a href='{{unsubscribe_url}}'>here</a> to opt out</p>",
                body_text="Sale",
            )
        )
        await session.commit()
        template_id = t.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Validate endpoint
        val_res = await client.post(
            "/templates/validate",
            json={
                "subject": "Hi {{first_name}}",
                "body_html": "<p>Hello {{company_name}}</p>",
            },
            cookies=cookies,
        )
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["valid"] is True
        assert len(val_data["warnings"]) > 0

        # Invalid token validation
        inv_val_res = await client.post(
            "/templates/validate",
            json={
                "subject": "Hi {{unknown_token_abc}}",
                "body_html": "<p>Content</p>",
            },
            cookies=cookies,
        )
        assert inv_val_res.status_code == 422

        # Duplicate template endpoint
        dup_res = await client.post(f"/templates/{template_id}/duplicate", cookies=cookies)
        assert dup_res.status_code == 201
        dup_data = dup_res.json()
        assert dup_data["name"] == "Original Promo (Copy)"
        assert dup_data["current_version"]["subject"] == "Big Sale {{first_name}}"

    # Clean up
    async with async_session_factory() as session:
        await session.execute(
            delete(EmailTemplate).where(
                EmailTemplate.account_id == account_id,
                EmailTemplate.name.in_(["Original Promo", "Original Promo (Copy)"]),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_analytics_timeseries_comparison_and_export(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
):
    account_id = await account_factory()
    admin_id = await user_factory(role_name="Admin", account_id=account_id)
    app = create_app()
    cookies = _access_token_cookie(admin_id)

    async with async_session_factory() as session:
        conn = EmailProviderConnection(
            account_id=account_id,
            name="Analytics Conn",
            provider="CUSTOM_SMTP",
            smtp_host="mail.test.local",
            smtp_port=587,
            smtp_username="usr",
            smtp_password_encrypted=encrypt_secret("pw"),
        )
        session.add(conn)
        await session.flush()
        identity = SenderIdentity(
            account_id=account_id,
            email_provider_connection_id=conn.id,
            from_email="sender@analytics.test",
            from_name="Analytics Test",
        )
        session.add(identity)
        await session.flush()

        campaign = Campaign(
            account_id=account_id,
            name="Analytics Test Campaign",
            subject="Analytics Test",
            body_html="<p>Analytics</p>",
            sender_identity_id=identity.id,
            recipient_type="ALL_CONTACTS",
            status="SENT",
        )
        session.add(campaign)
        await session.flush()

        c1 = Contact(
            account_id=account_id, email="recip1@test.com", first_name="Recip", last_name="One"
        )
        c2 = Contact(
            account_id=account_id, email="recip2@test.com", first_name="Recip", last_name="Two"
        )
        session.add_all([c1, c2])
        await session.flush()

        recip1 = CampaignRecipient(
            account_id=account_id,
            campaign_id=campaign.id,
            contact_id=c1.id,
            email="recip1@test.com",
            status="SENT",
        )
        recip2 = CampaignRecipient(
            account_id=account_id,
            campaign_id=campaign.id,
            contact_id=c2.id,
            email="recip2@test.com",
            status="SENT",
        )
        session.add_all([recip1, recip2])
        await session.flush()

        deliv1 = MessageDelivery(
            account_id=account_id,
            campaign_recipient_id=recip1.id,
            status="DELIVERED",
            delivered_at=datetime(2026, 9, 16, 10, 0, 0, tzinfo=UTC),
        )
        deliv2 = MessageDelivery(
            account_id=account_id,
            campaign_recipient_id=recip2.id,
            status="BOUNCED",
            bounced_at=datetime(2026, 9, 16, 10, 5, 0, tzinfo=UTC),
        )
        session.add_all([deliv1, deliv2])
        await session.flush()

        event1 = EmailEvent(
            account_id=account_id,
            message_delivery_id=deliv1.id,
            event_type="OPENED",
            occurred_at=datetime(2026, 9, 16, 10, 15, 0, tzinfo=UTC),
            event_metadata={},
        )
        session.add(event1)
        await session.commit()
        campaign_id = campaign.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Report
        rep_res = await client.get(f"/campaigns/{campaign_id}/report", cookies=cookies)
        assert rep_res.status_code == 200
        rep = rep_res.json()
        assert rep["sent"] == 2
        assert rep["delivered"] == 1
        assert rep["bounced"] == 1
        assert rep["opened"] == 1
        assert rep["open_rate_pct"] == 100.0
        assert rep["bounce_rate_pct"] == 50.0

        # Timeseries
        ts_res = await client.get(f"/campaigns/{campaign_id}/analytics/timeseries", cookies=cookies)
        assert ts_res.status_code == 200
        ts = ts_res.json()
        assert "points" in ts
        assert len(ts["points"]) >= 1
        assert ts["points"][0]["opened"] == 1

        # Comparison
        comp_res = await client.get(
            f"/campaigns/{campaign_id}/analytics/comparison", cookies=cookies
        )
        assert comp_res.status_code == 200
        comp = comp_res.json()
        assert comp["campaign_id"] == str(campaign_id)
        assert comp["recipient_count"] == 2
        assert comp["campaign_open_rate_pct"] == 100.0

        # CSV Export
        exp_res = await client.get(f"/campaigns/{campaign_id}/analytics/export", cookies=cookies)
        assert exp_res.status_code == 200
        assert "text/csv" in exp_res.headers["content-type"]
        csv_text = exp_res.text
        assert "Recipient Email,Recipient Status,Delivery Status" in csv_text
        assert "recip1@test.com" in csv_text
        assert "recip2@test.com" in csv_text

    # Clean up
    async with async_session_factory() as session:
        await session.execute(delete(Campaign).where(Campaign.id == campaign_id))
        await session.execute(delete(SenderIdentity).where(SenderIdentity.id == identity.id))
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.id == conn.id)
        )
        await session.commit()


@pytest.mark.asyncio
async def test_analytics_and_templates_multi_tenant_isolation(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
):
    account_id = await account_factory()
    admin_id = await user_factory(role_name="Admin", account_id=account_id)
    other_account_id = await account_factory()
    app = create_app()
    cookies = _access_token_cookie(admin_id)

    async with async_session_factory() as session:
        other_tpl = EmailTemplate(account_id=other_account_id, name="Other Tenant Template")
        session.add(other_tpl)
        await session.flush()
        session.add(
            EmailTemplateVersion(
                account_id=other_account_id,
                template_id=other_tpl.id,
                version_number=1,
                subject="Secret",
                body_html="<p>Secret</p>",
            )
        )
        conn = EmailProviderConnection(
            account_id=other_account_id,
            name="Other Conn",
            provider="CUSTOM_SMTP",
            smtp_host="mail.other.local",
            smtp_port=587,
            smtp_username="usr",
            smtp_password_encrypted=encrypt_secret("pw"),
        )
        session.add(conn)
        await session.flush()
        ident = SenderIdentity(
            account_id=other_account_id,
            email_provider_connection_id=conn.id,
            from_email="other@test.local",
            from_name="Other",
        )
        session.add(ident)
        await session.flush()
        other_cmp = Campaign(
            account_id=other_account_id,
            name="Other Campaign",
            subject="Other Subject",
            body_html="<p>Other</p>",
            sender_identity_id=ident.id,
            recipient_type="ALL_CONTACTS",
            status="SENT",
        )
        session.add(other_cmp)
        await session.commit()
        other_tpl_id = other_tpl.id
        other_cmp_id = other_cmp.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        dup_res = await client.post(f"/templates/{other_tpl_id}/duplicate", cookies=cookies)
        assert dup_res.status_code == 404

        rep_res = await client.get(f"/campaigns/{other_cmp_id}/report", cookies=cookies)
        assert rep_res.status_code == 404

        ts_res = await client.get(
            f"/campaigns/{other_cmp_id}/analytics/timeseries", cookies=cookies
        )
        assert ts_res.status_code == 404

        exp_res = await client.get(f"/campaigns/{other_cmp_id}/analytics/export", cookies=cookies)
        assert exp_res.status_code == 404

    # Clean up
    async with async_session_factory() as session:
        await session.execute(delete(Campaign).where(Campaign.id == other_cmp_id))
        await session.execute(delete(SenderIdentity).where(SenderIdentity.id == ident.id))
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.id == conn.id)
        )
        await session.execute(delete(EmailTemplate).where(EmailTemplate.id == other_tpl_id))
        await session.commit()


@pytest.mark.asyncio
async def test_duplicate_webhook_handling_idempotency(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
):
    """Verifies that redelivered webhooks with identical event payload are idempotent."""
    account_id = await account_factory()
    admin_id = await user_factory(role_name="Admin", account_id=account_id)
    app = create_app()

    async with async_session_factory() as session:
        conn = EmailProviderConnection(
            account_id=account_id,
            name="Postmark Webhook Test",
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
            webhook_username="wh-user",
            webhook_password_encrypted=encrypt_secret("wh-pass"),
        )
        session.add(conn)
        await session.flush()
        identity = SenderIdentity(
            account_id=account_id,
            email_provider_connection_id=conn.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.flush()

        contact = Contact(account_id=account_id, email="wh_test@example.com")
        session.add(contact)
        await session.flush()

        campaign = Campaign(
            account_id=account_id,
            name="Webhook Test Campaign",
            subject="Test Subject",
            body_html="<p>Test</p>",
            sender_identity_id=identity.id,
            recipient_type="ALL_CONTACTS",
            created_by_user_id=admin_id,
            status="SENDING",
        )
        session.add(campaign)
        await session.flush()

        recipient = CampaignRecipient(
            account_id=account_id,
            campaign_id=campaign.id,
            contact_id=contact.id,
            email="wh_test@example.com",
            status="SENT",
        )
        session.add(recipient)
        await session.flush()

        delivery = MessageDelivery(
            account_id=account_id,
            campaign_recipient_id=recipient.id,
            provider_message_id="pm-dedup-123",
            status="SENT",
        )
        session.add(delivery)
        await session.commit()
        delivery_id = delivery.id
        campaign_id = campaign.id

    webhook_payload = {
        "RecordType": "Delivery",
        "MessageID": "pm-dedup-123",
        "Recipient": "wh_test@example.com",
        "DeliveredAt": "2026-09-16T12:00:00Z",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First delivery webhook
        res1 = await client.post(
            "/webhooks/postmark",
            json=webhook_payload,
            auth=("wh-user", "wh-pass"),
        )
        assert res1.status_code == 200

        # Duplicate webhook (identical payload)
        res2 = await client.post(
            "/webhooks/postmark",
            json=webhook_payload,
            auth=("wh-user", "wh-pass"),
        )
        assert res2.status_code == 200

    async with async_session_factory() as session:
        events = (
            (
                await session.execute(
                    select(EmailEvent).where(EmailEvent.message_delivery_id == delivery_id)
                )
            )
            .scalars()
            .all()
        )
        # Ensure exactly one event was recorded despite duplicate webhook submission
        assert len(events) == 1
        assert events[0].event_type == "DELIVERED"

        # Clean up
        await session.execute(delete(Campaign).where(Campaign.id == campaign_id))
        await session.execute(delete(Contact).where(Contact.id == contact.id))
        await session.execute(delete(SenderIdentity).where(SenderIdentity.id == identity.id))
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.id == conn.id)
        )
        await session.commit()
