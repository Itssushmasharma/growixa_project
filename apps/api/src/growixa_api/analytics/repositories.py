import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery, UnsubscribeEvent


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

    unsub_result = await session.execute(
        select(func.count(UnsubscribeEvent.id)).where(UnsubscribeEvent.campaign_id == campaign_id)
    )
    unsub_count = unsub_result.scalar_one()

    delivered = status_counts.get("DELIVERED", 0) + status_counts.get("SENT", 0)
    bounced = status_counts.get("BOUNCED", 0)
    complained = status_counts.get("COMPLAINED", 0)
    opened = event_counts.get("OPENED", (0, 0))[0]
    total_opened = event_counts.get("OPENED", (0, 0))[1]
    clicked = event_counts.get("CLICKED", (0, 0))[0]
    total_clicked = event_counts.get("CLICKED", (0, 0))[1]

    open_rate_pct = round((opened / delivered) * 100, 1) if delivered > 0 else None
    click_rate_pct = round((clicked / delivered) * 100, 1) if delivered > 0 else None
    click_to_open_rate_pct = round((clicked / opened) * 100, 1) if opened > 0 else None
    bounce_rate_pct = round((bounced / sent) * 100, 1) if sent > 0 else None

    return {
        "sent": sent,
        "delivered": delivered,
        "bounced": bounced,
        "complained": complained,
        "opened": opened,
        "clicked": clicked,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
        "open_rate_pct": open_rate_pct,
        "click_rate_pct": click_rate_pct,
        "click_to_open_rate_pct": click_to_open_rate_pct,
        "bounce_rate_pct": bounce_rate_pct,
        "unsubscribe_count": unsub_count,
    }


async def get_campaign_timeseries_repo(
    session: AsyncSession, campaign_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Aggregates campaign events into hour-by-hour time series buckets."""
    bucket_expr = func.to_char(EmailEvent.occurred_at, 'YYYY-MM-DD"T"HH24:00:00"Z"')
    query = (
        select(
            bucket_expr.label("bucket"),
            EmailEvent.event_type,
            func.count(EmailEvent.id).label("count"),
        )
        .join(MessageDelivery, EmailEvent.message_delivery_id == MessageDelivery.id)
        .join(CampaignRecipient, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(CampaignRecipient.campaign_id == campaign_id)
        .group_by(bucket_expr, EmailEvent.event_type)
        .order_by(bucket_expr.asc())
    )
    result = await session.execute(query)

    buckets: dict[str, dict[str, int]] = {}
    for bucket_str, event_type, count in result.all():
        if bucket_str not in buckets:
            buckets[bucket_str] = {"delivered": 0, "opened": 0, "clicked": 0, "bounced": 0}
        if event_type == "DELIVERED":
            buckets[bucket_str]["delivered"] += count
        elif event_type == "OPENED":
            buckets[bucket_str]["opened"] += count
        elif event_type == "CLICKED":
            buckets[bucket_str]["clicked"] += count
        elif event_type == "BOUNCED":
            buckets[bucket_str]["bounced"] += count

    return [
        {
            "bucket": b,
            "delivered": counts["delivered"],
            "opened": counts["opened"],
            "clicked": counts["clicked"],
            "bounced": counts["bounced"],
        }
        for b, counts in sorted(buckets.items())
    ]


async def get_campaign_comparison_repo(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> dict[str, Any]:
    """Calculates campaign performance vs account average benchmarks across all sent campaigns."""
    campaign_res = await session.execute(
        select(Campaign).where(Campaign.account_id == account_id, Campaign.id == campaign_id)
    )
    campaign = campaign_res.scalar_one_or_none()
    if campaign is None:
        return {}

    current_report = await get_campaign_report_counts(session, campaign_id)

    # Fetch all sent campaigns in the account to calculate average benchmark
    other_campaigns_res = await session.execute(
        select(Campaign.id).where(
            Campaign.account_id == account_id,
            Campaign.status.in_(("SENT", "SENDING")),
        )
    )
    all_campaign_ids = other_campaigns_res.scalars().all()

    open_rates: list[float] = []
    click_rates: list[float] = []
    bounce_rates: list[float] = []

    for cid in all_campaign_ids:
        rep = await get_campaign_report_counts(session, cid)
        if rep.get("open_rate_pct") is not None:
            open_rates.append(rep["open_rate_pct"])
        if rep.get("click_rate_pct") is not None:
            click_rates.append(rep["click_rate_pct"])
        if rep.get("bounce_rate_pct") is not None:
            bounce_rates.append(rep["bounce_rate_pct"])

    avg_open = round(sum(open_rates) / len(open_rates), 1) if open_rates else None
    avg_click = round(sum(click_rates) / len(click_rates), 1) if click_rates else None
    avg_bounce = round(sum(bounce_rates) / len(bounce_rates), 1) if bounce_rates else None

    # Get total recipient count for this campaign
    recip_count_res = await session.execute(
        select(func.count(CampaignRecipient.id)).where(CampaignRecipient.campaign_id == campaign_id)
    )
    recip_count = recip_count_res.scalar_one()

    return {
        "campaign_id": campaign_id,
        "recipient_type": campaign.recipient_type,
        "recipient_count": recip_count,
        "campaign_open_rate_pct": current_report.get("open_rate_pct"),
        "campaign_click_rate_pct": current_report.get("click_rate_pct"),
        "campaign_bounce_rate_pct": current_report.get("bounce_rate_pct"),
        "account_avg_open_rate_pct": avg_open,
        "account_avg_click_rate_pct": avg_click,
        "account_avg_bounce_rate_pct": avg_bounce,
    }


async def get_campaign_recipients_export_data(
    session: AsyncSession, campaign_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Fetches exportable recipient delivery records for a campaign."""
    query = (
        select(
            CampaignRecipient.email,
            CampaignRecipient.status.label("recipient_status"),
            MessageDelivery.status.label("delivery_status"),
            MessageDelivery.sent_at,
            MessageDelivery.delivered_at,
            MessageDelivery.bounced_at,
        )
        .outerjoin(MessageDelivery, MessageDelivery.campaign_recipient_id == CampaignRecipient.id)
        .where(CampaignRecipient.campaign_id == campaign_id)
        .order_by(CampaignRecipient.email.asc())
    )
    res = await session.execute(query)
    rows = []
    for r in res.all():
        rows.append(
            {
                "email": r.email,
                "recipient_status": r.recipient_status,
                "delivery_status": r.delivery_status or "N/A",
                "sent_at": r.sent_at.isoformat() if r.sent_at else "",
                "delivered_at": r.delivered_at.isoformat() if r.delivered_at else "",
                "bounced_at": r.bounced_at.isoformat() if r.bounced_at else "",
            }
        )
    return rows
