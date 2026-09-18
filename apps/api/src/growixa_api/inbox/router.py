import uuid
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from pydantic import BaseModel
from growixa_api.inbox.models import InboxConversation, InboxMessage
from growixa_api.inbox.services import add_message

class SendMessageReq(BaseModel):
    content: str
    media_urls: list[str] | None = None

router = APIRouter(prefix="/inbox", tags=["Unified Inbox"])

@router.get("/conversations")
async def get_conversations(
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Fetch all unified conversations across channels.
    """
    result = await session.execute(
        select(InboxConversation)
        .where(InboxConversation.account_id == account_id)
        .order_by(InboxConversation.updated_at.desc())
    )
    return result.scalars().all()

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    payload: SendMessageReq,
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Send an outbound message in a conversation.
    """
    # Verify ownership
    convo = await session.get(InboxConversation, conversation_id)
    if not convo or convo.account_id != account_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    msg = await add_message(
        session=session,
        conversation_id=conversation_id,
        direction="OUTBOUND",
        content=payload.content,
        media_urls=payload.media_urls
    )
    await session.commit()
    return msg

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Fetch messages for a conversation.
    """
    convo = await session.get(InboxConversation, conversation_id)
    if not convo or convo.account_id != account_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    result = await session.execute(
        select(InboxMessage)
        .where(InboxMessage.conversation_id == conversation_id)
        .order_by(InboxMessage.created_at.asc())
    )
    return result.scalars().all()
