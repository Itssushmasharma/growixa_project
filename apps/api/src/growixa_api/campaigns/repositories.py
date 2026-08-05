import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import Campaign


async def create_campaign(session: AsyncSession, fields: dict[str, Any]) -> Campaign:
    campaign = Campaign(**fields)
    session.add(campaign)
    await session.flush()
    return campaign


async def get_campaign(session: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    return await session.get(Campaign, campaign_id)


async def list_campaigns(session: AsyncSession) -> Sequence[Campaign]:
    result = await session.execute(select(Campaign).order_by(Campaign.created_at))
    return result.scalars().all()


async def update_campaign_fields(
    session: AsyncSession, campaign: Campaign, fields: dict[str, Any]
) -> Campaign:
    for key, value in fields.items():
        setattr(campaign, key, value)
    await session.flush()
    return campaign
