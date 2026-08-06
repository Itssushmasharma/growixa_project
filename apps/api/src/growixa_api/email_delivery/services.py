import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import decrypt_secret
from growixa_api.campaigns.models import Campaign
from growixa_api.campaigns.repositories import get_campaign
from growixa_api.contacts.repositories import (
    create_suppression_entry,
    get_suppression_by_email,
)
from growixa_api.email_delivery.repositories import (
    create_email_event,
    create_unsubscribe_event,
    get_campaign_recipient,
    get_message_delivery_by_provider_message_id,
)
from growixa_api.email_delivery.schemas import PostmarkWebhookPayload
from growixa_api.integrations.repositories import (
    get_active_email_provider_connection,
    get_email_provider_connection,
    get_sender_identity,
)
from growixa_api.integrations.smtp_transport import send_email
from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import JobEnvelope

SEND_CAMPAIGN_QUEUE = "grx.email_delivery.send_campaign"

# Postmark's `RecordType` -> our `event_type`, and which ones also trigger auto-suppression
# (the recipient is known-undeliverable or has actively complained) per suppression_entries'
# existing `BOUNCED`/`COMPLAINED` reason values (defined since Slice 2, unused until now).
_EVENT_TYPE_BY_RECORD_TYPE = {
    "Delivery": "DELIVERED",
    "Open": "OPENED",
    "Click": "CLICKED",
    "Bounce": "BOUNCED",
    "SpamComplaint": "COMPLAINED",
}
_SUPPRESSION_REASON_BY_EVENT_TYPE = {"BOUNCED": "BOUNCED", "COMPLAINED": "COMPLAINED"}
_OCCURRED_AT_CANDIDATE_KEYS = (
    "DeliveredAt",
    "ReceivedAt",
    "BouncedAt",
    "ClickedAt",
    "OpenedAt",
    "SubmittedAt",
)


class CampaignNotFoundError(Exception):
    pass


class CampaignNotSendableError(Exception):
    """Raised when a send/test-send is attempted against a campaign that isn't (or is no
    longer) a DRAFT — sending twice, or sending mid-send, is not allowed."""


class InvalidWebhookRecordTypeError(Exception):
    pass


class CampaignRecipientNotFoundError(Exception):
    pass


async def _load_sendable_campaign(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    campaign = await get_campaign(session, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError
    return campaign


async def send_test_email(session: AsyncSession, campaign_id: uuid.UUID, to_email: str) -> None:
    """Sends the campaign's current draft content to a single address directly from the
    API request — deliberately synchronous and outside the job queue, since a test send
    doesn't touch campaign/recipient/delivery state at all (per SPRINT_03's acceptance
    criteria), unlike a real send which must never run inline (BACKGROUND_JOB_ARCHITECTURE.md)."""
    campaign = await _load_sendable_campaign(session, campaign_id)
    identity = await get_sender_identity(session, campaign.sender_identity_id)
    if identity is None:
        raise CampaignNotFoundError
    connection = await get_email_provider_connection(session, identity.email_provider_connection_id)
    if connection is None:
        raise CampaignNotFoundError
    await send_email(
        smtp_host=connection.smtp_host,
        smtp_port=connection.smtp_port,
        smtp_username=connection.smtp_username,
        smtp_password=decrypt_secret(connection.smtp_password_encrypted),
        from_email=identity.from_email,
        from_name=identity.from_name,
        to_email=to_email,
        subject=campaign.subject,
        body_html=campaign.body_html,
        body_text=campaign.body_text,
    )


async def trigger_campaign_send(
    session: AsyncSession, campaign_id: uuid.UUID, actor_id: uuid.UUID
) -> JobEnvelope:
    """Flips the campaign to SENDING and enqueues the real send as a worker job — never
    resolves recipients or sends anything inline in this request."""
    campaign = await _load_sendable_campaign(session, campaign_id)
    if campaign.status != "DRAFT":
        raise CampaignNotSendableError
    campaign.status = "SENDING"
    await session.commit()

    envelope = JobEnvelope(
        idempotency_key=f"campaign-send-{campaign.id}",
        job_type=SEND_CAMPAIGN_QUEUE,
        payload={"campaign_id": str(campaign.id)},
        created_by_user_id=actor_id,
    )
    await publish_job(SEND_CAMPAIGN_QUEUE, envelope)
    return envelope


async def verify_webhook_credentials(session: AsyncSession, username: str, password: str) -> bool:
    """Fails closed: no active Postmark connection, or a connection whose webhook
    credentials were never generated (pre-GRX-EMAIL-005 row), rejects every request.
    Constant-time comparison on both fields per THREAT_MODEL.md's T14.

    Hardcoded to the POSTMARK provider (not "whichever connection is active" — since
    GRX-EMAIL-011 that's ambiguous, as Custom SMTP can be independently active too):
    this route is `/webhooks/postmark`, so only Postmark's own credentials are ever
    relevant here. Custom SMTP has no webhook route at all — plain SMTP has no
    bounce/complaint/open/click callback mechanism to receive.
    """
    connection = await get_active_email_provider_connection(session, provider="POSTMARK")
    if (
        connection is None
        or connection.webhook_username is None
        or connection.webhook_password_encrypted is None
    ):
        return False
    expected_password = decrypt_secret(connection.webhook_password_encrypted)
    username_ok = secrets.compare_digest(username, connection.webhook_username)
    password_ok = secrets.compare_digest(password, expected_password)
    return username_ok and password_ok


def _extract_occurred_at(payload: PostmarkWebhookPayload) -> datetime:
    extra = payload.model_extra or {}
    for key in _OCCURRED_AT_CANDIDATE_KEYS:
        value = extra.get(key)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
    return datetime.now(UTC)


async def record_webhook_event(session: AsyncSession, payload: PostmarkWebhookPayload) -> None:
    """Processes one Postmark webhook event. Silently no-ops (rather than erroring) when
    `MessageID` doesn't match any known delivery — a redelivery race, a message this
    system didn't send, or (per AGENT_HANDOFF.md's evidence gap) an unverified payload
    shape are all treated the same: Postmark expects a 200, not a 4xx, either way."""
    event_type = _EVENT_TYPE_BY_RECORD_TYPE.get(payload.RecordType)
    if event_type is None:
        return

    delivery = await get_message_delivery_by_provider_message_id(session, payload.MessageID)
    if delivery is None:
        return

    occurred_at = _extract_occurred_at(payload)
    await create_email_event(
        session,
        {
            "message_delivery_id": delivery.id,
            "event_type": event_type,
            "occurred_at": occurred_at,
            "event_metadata": payload.model_extra or {},
        },
    )

    if event_type == "DELIVERED":
        delivery.status = "DELIVERED"
        delivery.delivered_at = occurred_at
    elif event_type == "BOUNCED":
        delivery.status = "BOUNCED"
        delivery.bounced_at = occurred_at
    elif event_type == "COMPLAINED":
        delivery.status = "COMPLAINED"

    suppression_reason = _SUPPRESSION_REASON_BY_EVENT_TYPE.get(event_type)
    if suppression_reason is not None and payload.Recipient:
        await _upsert_suppression(session, email=payload.Recipient, reason=suppression_reason)

    await session.commit()


async def _upsert_suppression(
    session: AsyncSession, *, email: str, reason: str, contact_id: uuid.UUID | None = None
) -> None:
    existing = await get_suppression_by_email(session, email)
    if existing is None:
        await create_suppression_entry(
            session, email=email, reason=reason, contact_id=contact_id, suppressed_by_user_id=None
        )
    else:
        existing.reason = reason
        existing.suppressed_at = datetime.now(UTC)
        if contact_id is not None:
            existing.contact_id = contact_id


async def record_unsubscribe(session: AsyncSession, campaign_recipient_id: uuid.UUID) -> None:
    """A recipient clicking the unsubscribe link in a specific send — distinct from a
    Postmark-reported bounce/complaint. Records the audit trail row and (in the same
    transaction) suppresses the address, reusing Slice 2's suppression infrastructure
    per DATA_MODEL.md's `unsubscribe_events` note. No actor_id: this is a public,
    unauthenticated action taken by the recipient, not an admin."""
    recipient = await get_campaign_recipient(session, campaign_recipient_id)
    if recipient is None:
        raise CampaignRecipientNotFoundError

    await create_unsubscribe_event(
        session,
        {
            "contact_id": recipient.contact_id,
            "campaign_id": recipient.campaign_id,
            "email": recipient.email,
        },
    )
    await _upsert_suppression(
        session, email=recipient.email, reason="UNSUBSCRIBED", contact_id=recipient.contact_id
    )
    await session.commit()
