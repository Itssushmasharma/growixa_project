import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery


async def create_campaign(session: AsyncSession, fields: dict[str, Any]) -> Campaign:
    campaign = Campaign(**fields)
    session.add(campaign)
    await session.flush()
    return campaign


async def get_campaign(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> Campaign | None:
    result = await session.execute(
        select(Campaign).where(Campaign.account_id == account_id, Campaign.id == campaign_id)
    )
    return result.scalar_one_or_none()


async def list_campaigns(session: AsyncSession, account_id: uuid.UUID) -> Sequence[Campaign]:
    result = await session.execute(
        select(Campaign).where(Campaign.account_id == account_id).order_by(Campaign.created_at)
    )
    return result.scalars().all()


async def get_campaigns_metrics_batch(
    session: AsyncSession, account_id: uuid.UUID, campaign_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict[str, Any]]:
    if not campaign_ids:
        return {}

    sent_result = await session.execute(
        select(CampaignRecipient.campaign_id, func.count(CampaignRecipient.id))
        .where(
            CampaignRecipient.account_id == account_id,
            CampaignRecipient.campaign_id.in_(campaign_ids),
            CampaignRecipient.status == "SENT",
        )
        .group_by(CampaignRecipient.campaign_id)
    )
    sent_counts = {row[0]: row[1] for row in sent_result.all()}

    delivered_result = await session.execute(
        select(CampaignRecipient.campaign_id, func.count(MessageDelivery.id))
        .join(MessageDelivery, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(
            CampaignRecipient.account_id == account_id,
            CampaignRecipient.campaign_id.in_(campaign_ids),
            MessageDelivery.status.in_(("SENT", "DELIVERED")),
        )
        .group_by(CampaignRecipient.campaign_id)
    )
    delivered_counts = {row[0]: row[1] for row in delivered_result.all()}

    opened_result = await session.execute(
        select(
            CampaignRecipient.campaign_id,
            func.count(func.distinct(EmailEvent.message_delivery_id)),
            func.count(EmailEvent.id),
        )
        .join(MessageDelivery, EmailEvent.message_delivery_id == MessageDelivery.id)
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(
            CampaignRecipient.account_id == account_id,
            CampaignRecipient.campaign_id.in_(campaign_ids),
            EmailEvent.event_type == "OPENED",
        )
        .group_by(CampaignRecipient.campaign_id)
    )
    opened_counts = {row[0]: (row[1], row[2]) for row in opened_result.all()}

    clicked_result = await session.execute(
        select(
            CampaignRecipient.campaign_id,
            func.count(func.distinct(EmailEvent.message_delivery_id)),
            func.count(EmailEvent.id),
        )
        .join(MessageDelivery, EmailEvent.message_delivery_id == MessageDelivery.id)
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(
            CampaignRecipient.account_id == account_id,
            CampaignRecipient.campaign_id.in_(campaign_ids),
            EmailEvent.event_type == "CLICKED",
        )
        .group_by(CampaignRecipient.campaign_id)
    )
    clicked_counts = {row[0]: (row[1], row[2]) for row in clicked_result.all()}

    stats: dict[uuid.UUID, dict[str, Any]] = {}
    for cid in campaign_ids:
        sent = sent_counts.get(cid, 0)
        delivered = delivered_counts.get(cid, 0)
        opened = opened_counts.get(cid, (0, 0))[0]
        total_opened = opened_counts.get(cid, (0, 0))[1]
        clicked = clicked_counts.get(cid, (0, 0))[0]
        total_clicked = clicked_counts.get(cid, (0, 0))[1]
        open_rate = (
            round(opened / delivered * 100, 1) if delivered > 0 else (0.0 if sent > 0 else None)
        )
        click_rate = (
            round(clicked / delivered * 100, 1) if delivered > 0 else (0.0 if sent > 0 else None)
        )
        ctor = round(clicked / opened * 100, 1) if opened > 0 else None
        stats[cid] = {
            "sent_count": sent,
            "delivered_count": delivered,
            "opened_count": opened,
            "clicked_count": clicked,
            "total_opened_count": total_opened,
            "total_clicked_count": total_clicked,
            "open_rate_pct": open_rate,
            "click_rate_pct": click_rate,
            "click_to_open_rate_pct": ctor,
        }
    return stats



async def update_campaign_fields(
    session: AsyncSession, campaign: Campaign, fields: dict[str, Any]
) -> Campaign:
    for key, value in fields.items():
        setattr(campaign, key, value)
    await session.flush()
    return campaign
