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


async def update_campaign_fields(
    session: AsyncSession, campaign: Campaign, fields: dict[str, Any]
) -> Campaign:
    for key, value in fields.items():
        setattr(campaign, key, value)
    await session.flush()
    return campaign
