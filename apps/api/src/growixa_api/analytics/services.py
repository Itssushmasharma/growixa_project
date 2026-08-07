import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.analytics.repositories import get_campaign_report_counts
from growixa_api.campaigns.services import CampaignNotFoundError, get_campaign_or_raise

__all__ = ["CampaignNotFoundError", "get_campaign_report"]


async def get_campaign_report(
    session: AsyncSession, account_id: uuid.UUID, campaign_id: uuid.UUID
) -> dict[str, object]:
    await get_campaign_or_raise(session, account_id, campaign_id)
    counts = await get_campaign_report_counts(session, campaign_id)
    return {"campaign_id": campaign_id, **counts}
