"""send_campaign job handler integration tests (GRX-EMAIL-004, worker side).

Integration-tier: exercises the real Postgres database growixa_api's migrations created
(apps/worker/.env points at the same Compose instance apps/api uses). The real SMTP
transport is monkeypatched — no live Postmark account available, see AGENT_HANDOFF.md for
the documented evidence gap.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker import send_campaign as send_campaign_module
from growixa_worker.config import get_settings
from growixa_worker.db import get_session_factory
from growixa_worker.email_sender import EmailSendError
from growixa_worker.models import (
    AccountSubscription,
    Campaign,
    CampaignRecipient,
    CampaignVersion,
    CompanyProfile,
    ConsentRecord,
    Contact,
    ContactCustomField,
    ContactFieldValue,
    ContactList,
    ContactListMember,
    DeliveryAttempt,
    EmailProviderConnection,
    MessageDelivery,
    Segment,
    SegmentMember,
    SegmentRule,
    SenderIdentity,
    SuppressionEntry,
    UsageRecord,
)
from growixa_worker.send_campaign import handle_send_campaign

# The seed account every GRX-SAAS-001 migration backfills pre-existing data into --
# guaranteed to exist in any migrated DB, so worker tests (which have no Account model
# of their own to create a fresh one) reuse it rather than needing a real accounts insert.
_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _encrypt(plaintext: str) -> str:
    return Fernet(get_settings().encryption_key.encode()).encrypt(plaintext.encode()).decode()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        await _cleanup(session)
        yield session
        await _cleanup(session)


async def _create_sender_identity(session: AsyncSession) -> uuid.UUID:
    connection = EmailProviderConnection(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        name="Worker Postmark",
        provider="POSTMARK",
        smtp_host="smtp.postmarkapp.com",
        smtp_port=587,
        smtp_username="token",
        smtp_password_encrypted=_encrypt("fake-smtp-password"),
    )
    session.add(connection)
    await session.flush()
    identity = SenderIdentity(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        email_provider_connection_id=connection.id,
        from_email="hello@growixa.local",
        from_name="Growixa",
    )
    session.add(identity)
    await session.commit()
    return identity.id


async def _create_contact(
    session: AsyncSession,
    email: str,
    *,
    status: str = "ACTIVE",
    deleted_at: datetime | None = None,
) -> uuid.UUID:
    contact = Contact(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        email=email,
        status=status,
        deleted_at=deleted_at,
    )
    session.add(contact)
    await session.flush()
    return contact.id


async def _create_campaign(
    session: AsyncSession,
    sender_identity_id: uuid.UUID,
    *,
    recipient_type: str,
    recipient_segment_id: uuid.UUID | None = None,
    recipient_list_id: uuid.UUID | None = None,
) -> uuid.UUID:
    campaign = Campaign(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        name="Test Campaign",
        subject="Hello",
        body_html="<p>hi</p>",
        sender_identity_id=sender_identity_id,
        recipient_type=recipient_type,
        recipient_segment_id=recipient_segment_id,
        recipient_list_id=recipient_list_id,
        status="SENDING",
    )
    session.add(campaign)
    await session.commit()
    return campaign.id


async def _cleanup(session: AsyncSession) -> None:
    await session.rollback()
    await session.execute(delete(DeliveryAttempt))
    await session.execute(delete(MessageDelivery))
    await session.execute(delete(CampaignRecipient))
    await session.execute(delete(CampaignVersion))
    await session.execute(delete(Campaign))
    await session.execute(delete(SegmentRule))
    await session.execute(delete(SegmentMember))
    await session.execute(delete(Segment))
    await session.execute(delete(ContactListMember))
    await session.execute(delete(ContactList))
    await session.execute(delete(ConsentRecord))
    await session.execute(delete(SuppressionEntry))
    await session.execute(delete(ContactFieldValue))
    await session.execute(delete(ContactCustomField))
    await session.execute(delete(CompanyProfile))
    await session.execute(delete(Contact))
    await session.execute(delete(SenderIdentity))
    await session.execute(delete(EmailProviderConnection))
    await session.execute(delete(UsageRecord))
    # The seed account's account_subscriptions row is shared across every test run
    # (GRX-BILL-002's backfill, not something this suite creates/deletes itself) --
    # reset its GRX-BILL-005 email counter so repeated runs don't accumulate real
    # quota usage against it and eventually start failing sends non-deterministically.
    await session.execute(
        update(AccountSubscription)
        .where(AccountSubscription.account_id == _ACCOUNT_ID)
        .values(period_email_used=0)
    )
    await session.commit()


@pytest.mark.integration
async def test_all_contacts_send_creates_deliveries_and_snapshot(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "active1@example.com")
        await _create_contact(session, "active2@example.com")
        await _create_contact(session, "archived@example.com", status="ARCHIVED")
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert sorted(sent_to) == ["active1@example.com", "active2@example.com"]

        campaign = await session.get(Campaign, campaign_id)
        assert campaign is not None
        assert campaign.status == "SENT"
        assert campaign.sent_at is not None

        version_result = await session.execute(
            select(CampaignVersion).where(CampaignVersion.campaign_id == campaign_id)
        )
        versions = version_result.scalars().all()
        assert len(versions) == 1
        assert versions[0].recipient_count == 2

        recipients_result = await session.execute(
            select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id)
        )
        recipients = recipients_result.scalars().all()
        assert {r.status for r in recipients} == {"SENT"}

        usage_result = await session.execute(
            select(UsageRecord).where(UsageRecord.operation_type == "email.sent")
        )
        usage_records = usage_result.scalars().all()
        assert len(usage_records) == 1
        assert float(usage_records[0].quantity) == 2.0
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_suppressed_and_withdrawn_consent_contacts_are_excluded(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        eligible_id = await _create_contact(session, "eligible@example.com")
        suppressed_id = await _create_contact(session, "suppressed@example.com")
        withdrawn_id = await _create_contact(session, "withdrawn@example.com")

        session.add(
            SuppressionEntry(
                id=uuid.uuid4(),
                account_id=_ACCOUNT_ID,
                email="suppressed@example.com",
                reason="MANUAL",
            )
        )
        session.add(
            ConsentRecord(
                id=uuid.uuid4(),
                account_id=_ACCOUNT_ID,
                contact_id=withdrawn_id,
                channel="EMAIL",
                status="WITHDRAWN",
                recorded_at=datetime.now(UTC),
            )
        )
        await session.commit()

        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert sent_to == ["eligible@example.com"]

        recipients_result = await session.execute(
            select(CampaignRecipient)
            .where(CampaignRecipient.campaign_id == campaign_id)
            .order_by(CampaignRecipient.email)
        )
        by_email = {r.email: r.status for r in recipients_result.scalars().all()}
        assert by_email == {
            "eligible@example.com": "SENT",
            "suppressed@example.com": "SUPPRESSED",
            "withdrawn@example.com": "SUPPRESSED",
        }

        version_result = await session.execute(
            select(CampaignVersion).where(CampaignVersion.campaign_id == campaign_id)
        )
        version = version_result.scalar_one()
        assert version.recipient_count == 3

        _ = eligible_id, suppressed_id
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_saved_segment_and_list_targeting_resolve_correctly(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        in_segment_id = await _create_contact(session, "in-segment@example.com")
        await _create_contact(session, "not-in-segment@example.com")
        in_list_id = await _create_contact(session, "in-list@example.com")

        segment = Segment(
            id=uuid.uuid4(), account_id=_ACCOUNT_ID, name="Test Segment", type="SAVED"
        )
        session.add(segment)
        contact_list = ContactList(id=uuid.uuid4(), account_id=_ACCOUNT_ID, name="Test List")
        session.add(contact_list)
        await session.flush()
        session.add(
            SegmentMember(account_id=_ACCOUNT_ID, segment_id=segment.id, contact_id=in_segment_id)
        )
        session.add(
            ContactListMember(
                account_id=_ACCOUNT_ID, list_id=contact_list.id, contact_id=in_list_id
            )
        )
        await session.commit()

        segment_campaign_id = await _create_campaign(
            session,
            sender_identity_id,
            recipient_type="SEGMENT",
            recipient_segment_id=segment.id,
        )
        await handle_send_campaign(session, {"campaign_id": segment_campaign_id})
        assert sent_to == ["in-segment@example.com"]

        sent_to.clear()
        list_campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="LIST", recipient_list_id=contact_list.id
        )
        await handle_send_campaign(session, {"campaign_id": list_campaign_id})
        assert sent_to == ["in-list@example.com"]
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_dynamic_segment_evaluates_rules_at_send_time(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "vip@example.com")
        await _create_contact(session, "regular@example.com")

        segment = Segment(
            id=uuid.uuid4(), account_id=_ACCOUNT_ID, name="VIP Segment", type="DYNAMIC"
        )
        session.add(segment)
        await session.flush()
        session.add(
            SegmentRule(
                id=uuid.uuid4(),
                account_id=_ACCOUNT_ID,
                segment_id=segment.id,
                field="email",
                operator="contains",
                value="vip",
            )
        )
        await session.commit()

        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="SEGMENT", recipient_segment_id=segment.id
        )
        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert sent_to == ["vip@example.com"]
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_smtp_failure_marks_recipient_and_delivery_failed(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _failing_send_email(**kwargs: object) -> None:
        raise EmailSendError("connection refused")

    monkeypatch.setattr(send_campaign_module, "send_email", _failing_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "bounce@example.com")
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        recipient_result = await session.execute(
            select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id)
        )
        recipient = recipient_result.scalar_one()
        assert recipient.status == "FAILED"

        delivery_result = await session.execute(
            select(MessageDelivery).where(MessageDelivery.campaign_recipient_id == recipient.id)
        )
        delivery = delivery_result.scalar_one()
        assert delivery.status == "FAILED"

        usage_result = await session.execute(
            select(UsageRecord).where(UsageRecord.operation_type == "email.sent")
        )
        usage_record = usage_result.scalar_one()
        assert float(usage_record.quantity) == 0.0
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_reprocessing_an_already_sent_campaign_is_a_noop(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    call_count = 0

    async def _fake_send_email(**kwargs: object) -> None:
        nonlocal call_count
        call_count += 1

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "once@example.com")
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})
        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert call_count == 1

        version_result = await session.execute(
            select(CampaignVersion).where(CampaignVersion.campaign_id == campaign_id)
        )
        assert len(version_result.scalars().all()) == 1
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_send_embeds_per_recipient_unsubscribe_link(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[dict[str, object]] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent.append(kwargs)

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "solo@example.com")
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert len(sent) == 1
        recipients_result = await session.execute(
            select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id)
        )
        recipient = recipients_result.scalar_one()

        expected_url = f"{get_settings().api_public_url}/unsubscribe/{recipient.id}"
        assert expected_url in str(sent[0]["body_html"])
        assert expected_url in str(sent[0]["body_text"])
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_send_includes_list_unsubscribe_headers(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RFC 8058 one-click unsubscribe (GRX-SAAS-013 ad hoc pass) -- Gmail/Yahoo's 2024+
    bulk-sender requirements, on top of the visible footer link tested above."""
    sent: list[dict[str, object]] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent.append(kwargs)

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "solo@example.com")
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert len(sent) == 1
        recipients_result = await session.execute(
            select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id)
        )
        recipient = recipients_result.scalar_one()

        expected_url = f"{get_settings().api_public_url}/unsubscribe/{recipient.id}"
        headers = sent[0]["extra_headers"]
        assert isinstance(headers, dict)
        assert headers["List-Unsubscribe"] == f"<{expected_url}>"
        assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_domain_suppressed_contacts_are_excluded(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "eligible@example.com")
        await _create_contact(session, "blocked@suppressed-domain.com")

        session.add(
            SuppressionEntry(
                id=uuid.uuid4(),
                account_id=_ACCOUNT_ID,
                domain="suppressed-domain.com",
                reason="MANUAL",
            )
        )
        await session.commit()

        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert sent_to == ["eligible@example.com"]

        recipients_result = await session.execute(
            select(CampaignRecipient)
            .where(CampaignRecipient.campaign_id == campaign_id)
            .order_by(CampaignRecipient.email)
        )
        by_email = {r.email: r.status for r in recipients_result.scalars().all()}
        assert by_email == {
            "blocked@suppressed-domain.com": "SUPPRESSED",
            "eligible@example.com": "SENT",
        }
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_soft_deleted_contacts_are_excluded_from_send(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "live@example.com")
        await _create_contact(session, "deleted@example.com", deleted_at=datetime.now(UTC))
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        assert sent_to == ["live@example.com"]
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_in_flight_emergency_cancellation_halts_worker_and_cancels_remaining_recipients(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_to: list[str] = []

    async def _fake_send_email_and_cancel_after_first(**kwargs: object) -> None:
        sent_to.append(str(kwargs["to_email"]))
        # Simulate user hitting Emergency Stop on the web UI after first recipient is sent
        campaign_db = await session.get(Campaign, campaign_id)
        if campaign_db:
            campaign_db.status = "CANCELLED"
            campaign_db.cancelled_at = datetime.now(UTC)

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email_and_cancel_after_first)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "recipient1@example.com")
        await _create_contact(session, "recipient2@example.com")
        await _create_contact(session, "recipient3@example.com")
        campaign_id = await _create_campaign(
            session, sender_identity_id, recipient_type="ALL_CONTACTS"
        )

        await handle_send_campaign(session, {"campaign_id": campaign_id})

        # Only recipient1 was sent before the emergency stop triggered
        assert sent_to == ["recipient1@example.com"]

        # Verify campaign status is CANCELLED
        camp_result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign_final = camp_result.scalar_one()
        assert campaign_final.status == "CANCELLED"
        assert campaign_final.cancelled_at is not None

        # Verify recipient 1 is SENT and remaining recipients 2 & 3 are CANCELLED
        recipients_result = await session.execute(
            select(CampaignRecipient)
            .where(CampaignRecipient.campaign_id == campaign_id)
            .order_by(CampaignRecipient.email)
        )
        statuses = {r.email: r.status for r in recipients_result.scalars().all()}
        assert statuses == {
            "recipient1@example.com": "SENT",
            "recipient2@example.com": "PENDING",
            "recipient3@example.com": "PENDING",
        }

        # Verify usage record only billed 1 email
        usage_result = await session.execute(
            select(UsageRecord).where(
                UsageRecord.account_id == _ACCOUNT_ID,
                UsageRecord.operation_type == "email.sent",
            )
        )
        usage_records = usage_result.scalars().all()
        assert len(usage_records) == 1
        assert float(usage_records[0].quantity) == 1.0
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_campaign_send_with_personalization_tokens_and_custom_fields(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_messages: list[dict[str, object]] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_messages.append(dict(kwargs))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        # Create company profile
        session.add(
            CompanyProfile(
                id=uuid.uuid4(),
                account_id=_ACCOUNT_ID,
                name="IITDEVELOPER",
                website="https://iitdeveloper.com",
            )
        )
        # Create sender identity
        sender_identity_id = await _create_sender_identity(session)

        # Create custom field "school_name"
        cf = ContactCustomField(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            key="school_name",
            label="School Name",
            field_type="TEXT",
            is_personalization_usable=True,
        )
        session.add(cf)
        await session.flush()

        # Create 2 contacts: one with custom field value, one without
        c1 = Contact(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            email="principal@school.edu",
            first_name="Dr. Smith",
            status="ACTIVE",
        )
        c2 = Contact(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            email="admin@academy.edu",
            first_name=None,  # Will test fallback default
            status="ACTIVE",
        )
        session.add_all([c1, c2])
        await session.flush()

        session.add(
            ContactFieldValue(
                account_id=_ACCOUNT_ID,
                contact_id=c1.id,
                field_id=cf.id,
                value="St. Mary's Academy",
            )
        )
        await session.commit()

        # Create campaign with subject and body using personalization
        campaign = Campaign(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            name="Personalized Admission Outreach",
            subject='How does {{school_name | default:"your school"}} look to a parent?',
            body_html=(
                '<p>Dear {{first_name | default:"Educator"}},</p><p>From {{company_name}}.</p>'
            ),
            body_text='Dear {{first_name | default:"Educator"}},\nFrom {{company_name}}.',
            sender_identity_id=sender_identity_id,
            recipient_type="ALL_CONTACTS",
            status="SENDING",
        )
        session.add(campaign)
        await session.commit()

        await handle_send_campaign(session, {"campaign_id": campaign.id})

        assert len(sent_messages) == 2
        msg_by_to = {str(m["to_email"]): m for m in sent_messages}

        # Contact 1: custom field resolved + first_name + company_name
        m1 = msg_by_to["principal@school.edu"]
        assert m1["subject"] == "How does St. Mary's Academy look to a parent?"
        assert "<p>Dear Dr. Smith,</p><p>From IITDEVELOPER.</p>" in str(m1["body_html"])
        assert "Dear Dr. Smith,\nFrom IITDEVELOPER." in str(m1["body_text"])

        # Contact 2: fallback defaults for school_name and first_name
        m2 = msg_by_to["admin@academy.edu"]
        assert m2["subject"] == "How does your school look to a parent?"
        assert "<p>Dear Educator,</p><p>From IITDEVELOPER.</p>" in str(m2["body_html"])
        assert "Dear Educator,\nFrom IITDEVELOPER." in str(m2["body_text"])
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_campaign_send_with_unknown_token_fails_validation_cleanly(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent_messages: list[dict[str, object]] = []

    async def _fake_send_email(**kwargs: object) -> None:
        sent_messages.append(dict(kwargs))

    monkeypatch.setattr(send_campaign_module, "send_email", _fake_send_email)

    try:
        sender_identity_id = await _create_sender_identity(session)
        await _create_contact(session, "test@example.com")

        # Campaign with unknown token "{{unknown_typo_token}}"
        campaign = Campaign(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            name="Broken Campaign",
            subject="Hello {{unknown_typo_token}}",
            body_html="<p>Content</p>",
            body_text=None,
            sender_identity_id=sender_identity_id,
            recipient_type="ALL_CONTACTS",
            status="SENDING",
        )
        session.add(campaign)
        await session.commit()

        await handle_send_campaign(session, {"campaign_id": campaign.id})

        # Nothing should have been sent
        assert len(sent_messages) == 0

        # Campaign status should be FAILED
        camp_result = await session.execute(select(Campaign).where(Campaign.id == campaign.id))
        assert camp_result.scalar_one().status == "FAILED"
    finally:
        await _cleanup(session)
