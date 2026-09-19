import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.repositories import get_account_id_for_user
from growixa_api.config import get_settings
from growixa_api.db import get_session
from growixa_api.inbox.models import InboxConversation, InboxMessage
from growixa_api.inbox.ws import manager
from growixa_api.permissions.dependencies import get_current_account_id, get_current_user_id


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
        raise HTTPException(status_code=404, detail="Conversation not found")

    raise HTTPException(
        503,
        detail={
            "code": "FEATURE_PENDING",
            "message": "Inbox delivery is pending provider integration. No message was sent.",
        },
    )


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
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await session.execute(
        select(InboxMessage)
        .where(InboxMessage.conversation_id == conversation_id)
        .order_by(InboxMessage.created_at.asc())
    )
    return result.scalars().all()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    # Browser cookies authenticate the connection; never trust query-string tenant IDs.
    if websocket.headers.get("origin") not in get_settings().cors_allowed_origins:
        raise WebSocketException(code=1008)
    try:
        user_id = await get_current_user_id(websocket)
        account_id = await get_account_id_for_user(session, user_id)
    except HTTPException as exc:
        raise WebSocketException(code=1008) from exc
    if account_id is None:
        raise WebSocketException(code=1008)
    requested_account = websocket.query_params.get("account_id")
    if requested_account is not None and requested_account != str(account_id):
        raise WebSocketException(code=1008)
    await manager.connect(websocket, account_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, account_id)
