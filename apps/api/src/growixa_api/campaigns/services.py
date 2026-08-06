import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import Campaign
from growixa_api.campaigns.repositories import (
    create_campaign as create_campaign_row,
)
from growixa_api.campaigns.repositories import (
    get_campaign,
    list_campaigns,
    update_campaign_fields,
)
from growixa_api.campaigns.schemas import CampaignIn, CampaignUpdateIn, ScheduleCampaignIn
from growixa_api.contacts.repositories import get_contact_list_by_id, get_segment_by_id
from growixa_api.integrations.repositories import get_sender_identity
from growixa_api.templates.repositories import get_template

VALID_RECIPIENT_TYPES = {"SEGMENT", "LIST", "ALL_CONTACTS"}


class CampaignNotFoundError(Exception):
    pass


class InvalidRecipientTargetError(Exception):
    pass


class SenderIdentityNotFoundError(Exception):
    pass


class TemplateNotFoundError(Exception):
    pass


class CampaignNotEditableError(Exception):
    """Raised when attempting to edit a campaign whose status has left DRAFT — draft
    content is only mutable up until sending starts, per DATA_MODEL.md."""


class CampaignAlreadyScheduledError(Exception):
    """Raised when scheduling a campaign that is not in DRAFT status."""


class CampaignNotCancellableError(Exception):
    """Raised when cancelling a campaign that is not in DRAFT or SCHEDULED status."""


async def _validate_recipient_target(
    session: AsyncSession,
    recipient_type: str,
    recipient_segment_id: uuid.UUID | None,
    recipient_list_id: uuid.UUID | None,
) -> None:
    if recipient_type not in VALID_RECIPIENT_TYPES:
        raise InvalidRecipientTargetError(f"Unknown recipient_type: {recipient_type}")

    if recipient_type == "SEGMENT":
        if recipient_segment_id is None or recipient_list_id is not None:
            raise InvalidRecipientTargetError(
                "recipient_segment_id must be set and recipient_list_id must be unset "
                "when recipient_type is SEGMENT"
            )
        if await get_segment_by_id(session, recipient_segment_id) is None:
            raise InvalidRecipientTargetError("recipient_segment_id does not exist")
    elif recipient_type == "LIST":
        if recipient_list_id is None or recipient_segment_id is not None:
            raise InvalidRecipientTargetError(
                "recipient_list_id must be set and recipient_segment_id must be unset "
                "when recipient_type is LIST"
            )
        if await get_contact_list_by_id(session, recipient_list_id) is None:
            raise InvalidRecipientTargetError("recipient_list_id does not exist")
    else:
        if recipient_segment_id is not None or recipient_list_id is not None:
            raise InvalidRecipientTargetError(
                "recipient_segment_id and recipient_list_id must both be unset "
                "when recipient_type is ALL_CONTACTS"
            )


async def create_campaign(session: AsyncSession, data: CampaignIn, actor_id: uuid.UUID) -> Campaign:
    if await get_sender_identity(session, data.sender_identity_id) is None:
        raise SenderIdentityNotFoundError
    if data.template_id is not None and await get_template(session, data.template_id) is None:
        raise TemplateNotFoundError
    await _validate_recipient_target(
        session, data.recipient_type, data.recipient_segment_id, data.recipient_list_id
    )
    return await create_campaign_row(
        session,
        {
            "name": data.name,
            "subject": data.subject,
            "body_html": data.body_html,
            "body_text": data.body_text,
            "template_id": data.template_id,
            "sender_identity_id": data.sender_identity_id,
            "recipient_type": data.recipient_type,
            "recipient_segment_id": data.recipient_segment_id,
            "recipient_list_id": data.recipient_list_id,
            "created_by_user_id": actor_id,
        },
    )


async def get_campaign_or_raise(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    campaign = await get_campaign(session, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError
    return campaign


async def list_all_campaigns(session: AsyncSession) -> Sequence[Campaign]:
    return await list_campaigns(session)


async def update_campaign(
    session: AsyncSession, campaign_id: uuid.UUID, data: CampaignUpdateIn
) -> Campaign:
    campaign = await get_campaign(session, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError
    if campaign.status != "DRAFT":
        raise CampaignNotEditableError

    fields = data.model_dump(exclude_unset=True)

    if "sender_identity_id" in fields and (
        await get_sender_identity(session, fields["sender_identity_id"]) is None
    ):
        raise SenderIdentityNotFoundError
    if (
        "template_id" in fields
        and fields["template_id"] is not None
        and await get_template(session, fields["template_id"]) is None
    ):
        raise TemplateNotFoundError

    if "recipient_type" in fields:
        recipient_type = fields["recipient_type"]
        recipient_segment_id = fields.get("recipient_segment_id")
        recipient_list_id = fields.get("recipient_list_id")
        await _validate_recipient_target(
            session, recipient_type, recipient_segment_id, recipient_list_id
        )
        # Force both explicitly into `fields` (even if the client didn't send them) so
        # switching recipient_type also clears whichever of segment_id/list_id no longer
        # applies, rather than leaving a stale reference from the previous type.
        fields["recipient_segment_id"] = recipient_segment_id
        fields["recipient_list_id"] = recipient_list_id

    campaign = await update_campaign_fields(session, campaign, fields)
    await session.commit()
    # `updated_at`'s server-side onupdate expires the attribute after an UPDATE commit;
    # refresh explicitly while still inside an awaited call (see contacts/services.py).
    await session.refresh(campaign)
    return campaign


async def schedule_campaign(
    session: AsyncSession, campaign_id: uuid.UUID, data: ScheduleCampaignIn
) -> Campaign:
    """Move a DRAFT campaign to SCHEDULED status.

    Only campaigns in DRAFT may be scheduled — calling this on a campaign
    that has already been scheduled, is currently dispatching, sent, cancelled,
    or failed raises ``CampaignAlreadyScheduledError``.

    ``data.scheduled_at`` must be strictly in the future (UTC); a past or
    present value raises ``ValueError``.
    """
    campaign = await get_campaign(session, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError
    if campaign.status != "DRAFT":
        raise CampaignAlreadyScheduledError(
            f"Campaign is in status '{campaign.status}' and cannot be scheduled"
        )
    if data.scheduled_at.astimezone(UTC) <= datetime.now(UTC):
        raise ValueError("scheduled_at must be a future datetime")

    campaign = await update_campaign_fields(
        session,
        campaign,
        {
            "status": "SCHEDULED",
            "scheduled_at": data.scheduled_at,
        },
    )
    await session.commit()
    await session.refresh(campaign)
    return campaign


async def cancel_campaign(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    """Cancel a DRAFT or SCHEDULED campaign before it is dispatched.

    Campaigns that are already DISPATCHING, SENDING, SENT, or FAILED cannot be
    cancelled (they are either mid-flight or complete) — raises
    ``CampaignNotCancellableError``.
    """
    campaign = await get_campaign(session, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError
    if campaign.status not in {"DRAFT", "SCHEDULED"}:
        raise CampaignNotCancellableError(
            f"Campaign is in status '{campaign.status}' and cannot be cancelled"
        )

    campaign = await update_campaign_fields(
        session,
        campaign,
        {
            "status": "CANCELLED",
            "cancelled_at": datetime.now(UTC),
        },
    )
    await session.commit()
    await session.refresh(campaign)
    return campaign
