import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from growixa_api.inbox.models import InboxConversation, InboxMessage

async def create_conversation(
    session: AsyncSession,
    account_id: uuid.UUID,
    channel: str,
    channel_identity_id: str,
    contact_id: uuid.UUID | None = None
) -> InboxConversation:
    convo = InboxConversation(
        account_id=account_id,
        channel=channel,
        channel_identity_id=channel_identity_id,
        contact_id=contact_id,
        status="OPEN"
    )
    session.add(convo)
    await session.flush()
    return convo

async def add_message(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    direction: str,
    content: str,
    media_urls: list[str] | None = None,
    provider_message_id: str | None = None
) -> InboxMessage:
    msg = InboxMessage(
        conversation_id=conversation_id,
        direction=direction,
        content=content,
        media_urls=media_urls or [],
        provider_message_id=provider_message_id
    )
    session.add(msg)
    await session.flush()
    return msg
