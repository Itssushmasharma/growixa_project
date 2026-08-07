import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.models import CampaignRecipient
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery, UnsubscribeEvent


async def get_message_delivery_by_provider_message_id(
    session: AsyncSession, account_id: uuid.UUID, provider_message_id: str
) -> MessageDelivery | None:
    result = await session.execute(
        select(MessageDelivery).where(
            MessageDelivery.account_id == account_id,
            MessageDelivery.provider_message_id == provider_message_id,
        )
    )
    return result.scalar_one_or_none()


async def create_email_event(session: AsyncSession, fields: dict[str, Any]) -> EmailEvent:
    event = EmailEvent(**fields)
    session.add(event)
    await session.flush()
    return event


async def create_unsubscribe_event(
    session: AsyncSession, fields: dict[str, Any]
) -> UnsubscribeEvent:
    event = UnsubscribeEvent(**fields)
    session.add(event)
    await session.flush()
    return event


async def get_campaign_recipient(
    session: AsyncSession, campaign_recipient_id: uuid.UUID
) -> CampaignRecipient | None:
    """Deliberately unscoped by account_id -- the sole caller is the public unsubscribe
    route, where the unguessable `campaign_recipient_id` UUID itself is the only
    credential (same security model as before GRX-SAAS-001). The returned row's own
    `account_id` is used downstream instead of being an input here."""
    return await session.get(CampaignRecipient, campaign_recipient_id)
