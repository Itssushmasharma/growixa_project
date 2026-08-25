import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import CampaignRecipient
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery


async def get_campaign_report_counts(
    session: AsyncSession, campaign_id: uuid.UUID
) -> dict[str, Any]:
    """`sent` comes from `campaign_recipients.status` (set once at send time and never
    touched again by webhook handling, so it stays a stable count even after a delivery
    later bounces). `delivered`/`bounced`/`complained` come from `message_deliveries.status`
    — a single mutable pointer, so this reflects each delivery's current terminal state.
    `opened`/`clicked` count distinct deliveries with at least one matching `email_events` row.
    `total_opened`/`total_clicked` count all raw events."""
    sent_result = await session.execute(
        select(func.count(CampaignRecipient.id)).where(
            CampaignRecipient.campaign_id == campaign_id,
            CampaignRecipient.status == "SENT",
        )
    )
    sent = sent_result.scalar_one()

    status_result = await session.execute(
        select(MessageDelivery.status, func.count(MessageDelivery.id))
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(CampaignRecipient.campaign_id == campaign_id)
        .group_by(MessageDelivery.status)
    )
    status_counts = {row[0]: row[1] for row in status_result.all()}

    event_result = await session.execute(
        select(
            EmailEvent.event_type,
            func.count(func.distinct(EmailEvent.message_delivery_id)),
            func.count(EmailEvent.id),
        )
        .join(MessageDelivery, EmailEvent.message_delivery_id == MessageDelivery.id)
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(CampaignRecipient.campaign_id == campaign_id)
        .group_by(EmailEvent.event_type)
    )
    event_counts = {row[0]: (row[1], row[2]) for row in event_result.all()}

    delivered = status_counts.get("DELIVERED", 0) + status_counts.get("SENT", 0)
    opened = event_counts.get("OPENED", (0, 0))[0]
    total_opened = event_counts.get("OPENED", (0, 0))[1]
    clicked = event_counts.get("CLICKED", (0, 0))[0]
    total_clicked = event_counts.get("CLICKED", (0, 0))[1]

    open_rate_pct = round((opened / delivered) * 100, 1) if delivered > 0 else None
    click_rate_pct = round((clicked / delivered) * 100, 1) if delivered > 0 else None
    click_to_open_rate_pct = round((clicked / opened) * 100, 1) if opened > 0 else None

    return {
        "sent": sent,
        "delivered": delivered,
        "bounced": status_counts.get("BOUNCED", 0),
        "complained": status_counts.get("COMPLAINED", 0),
        "opened": opened,
        "clicked": clicked,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
        "open_rate_pct": open_rate_pct,
        "click_rate_pct": click_rate_pct,
        "click_to_open_rate_pct": click_to_open_rate_pct,
    }
