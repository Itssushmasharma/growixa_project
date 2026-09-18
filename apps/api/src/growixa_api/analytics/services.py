import csv
import io
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.analytics.repositories import (
    get_campaign_comparison_repo,
    get_campaign_recipients_export_data,
    get_campaign_report_counts,
    get_campaign_timeseries_repo,
)
from growixa_api.campaigns.services import CampaignNotFoundError, get_campaign_or_raise

__all__ = [
    "CampaignNotFoundError",
    "export_campaign_csv",
    "get_campaign_comparison",
    "get_campaign_report",
    "get_campaign_timeseries",
]


async def get_campaign_report(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> dict[str, object]:
    await get_campaign_or_raise(session, account_id, campaign_id)
    counts = await get_campaign_report_counts(session, campaign_id)
    return {"campaign_id": campaign_id, **counts}


async def get_campaign_timeseries(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> dict[str, Any]:
    await get_campaign_or_raise(session, account_id, campaign_id)
    points = await get_campaign_timeseries_repo(session, campaign_id)
    return {"campaign_id": campaign_id, "points": points}


async def get_campaign_comparison(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> dict[str, Any]:
    await get_campaign_or_raise(session, account_id, campaign_id)
    comparison = await get_campaign_comparison_repo(session, account_id, campaign_id)
    return comparison


async def export_campaign_csv(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> str:
    await get_campaign_or_raise(session, account_id, campaign_id)
    rows = await get_campaign_recipients_export_data(session, campaign_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Recipient Email",
            "Recipient Status",
            "Delivery Status",
            "Sent At",
            "Delivered At",
            "Bounced At",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r["email"],
                r["recipient_status"],
                r["delivery_status"],
                r["sent_at"],
                r["delivered_at"],
                r["bounced_at"],
            ]
        )
    return output.getvalue()
