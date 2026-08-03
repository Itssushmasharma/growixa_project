import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import decrypt_secret
from growixa_api.campaigns.models import Campaign
from growixa_api.campaigns.repositories import get_campaign
from growixa_api.email_delivery.smtp_sender import send_email
from growixa_api.integrations.repositories import (
    get_email_provider_connection,
    get_sender_identity,
)
from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import JobEnvelope

SEND_CAMPAIGN_QUEUE = "grx.email_delivery.send_campaign"


class CampaignNotFoundError(Exception):
    pass


class CampaignNotSendableError(Exception):
    """Raised when a send/test-send is attempted against a campaign that isn't (or is no
    longer) a DRAFT — sending twice, or sending mid-send, is not allowed."""


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
