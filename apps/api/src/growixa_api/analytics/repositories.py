import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import CampaignRecipient
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery


async def get_campaign_report_counts(
    session: AsyncSession, campaign_id: uuid.UUID
) -> dict[str, int]:
    """`sent` comes from `campaign_recipients.status` (set once at send time and never
    touched again by webhook handling, so it stays a stable count even after a delivery
    later bounces). `delivered`/`bounced`/`complained` come from `message_deliveries.status`
    — a single mutable pointer, so this reflects each delivery's current terminal state.
    `opened`/`clicked` have no status of their own (only DELIVERED/BOUNCED/COMPLAINED ever
    update `message_deliveries.status`), so they're counted as distinct deliveries with at
    least one matching `email_events` row — a redelivered webhook event is a new row
    (insert-only), so counting rows directly would double-count a repeat notification."""
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
        select(EmailEvent.event_type, func.count(func.distinct(EmailEvent.message_delivery_id)))
        .join(MessageDelivery, EmailEvent.message_delivery_id == MessageDelivery.id)
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(CampaignRecipient.campaign_id == campaign_id)
        .group_by(EmailEvent.event_type)
    )
    event_counts = {row[0]: row[1] for row in event_result.all()}

    return {
        "sent": sent,
        "delivered": status_counts.get("DELIVERED", 0),
        "bounced": status_counts.get("BOUNCED", 0),
        "complained": status_counts.get("COMPLAINED", 0),
        "opened": event_counts.get("OPENED", 0),
        "clicked": event_counts.get("CLICKED", 0),
    }
