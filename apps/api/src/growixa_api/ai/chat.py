from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from growixa_api.db import get_session

router = APIRouter(prefix="/ai", tags=["ai-chat"])

class ChatMessageIn(BaseModel):
    message: str
    session_id: str | None = None

class ChatMessageOut(BaseModel):
    reply: str
    session_id: str

@router.post("/chat", response_model=ChatMessageOut)
async def ai_chat_route(
    payload: ChatMessageIn,
    session: AsyncSession = Depends(get_session),
) -> ChatMessageOut:
    """
    Endpoint for the AI Bot widget on the frontend.
    """
    user_msg = payload.message.lower().strip()
    session_id = payload.session_id or str(uuid.uuid4())
    
    if "pricing" in user_msg or "cost" in user_msg:
        reply = "Our pricing starts at $49/mo for the Pro plan. You can check out more details on our pricing page!"
    elif "contact" in user_msg or "support" in user_msg:
        reply = "You can reach our support team at support@growixa.com."
    elif "hi" in user_msg or "hello" in user_msg:
        reply = "Hello! I am Growixa AI. How can I help you grow your business today?"
    else:
        reply = "I'm still learning! But I can help you navigate our marketing OS. Could you rephrase your question?"

    return ChatMessageOut(reply=reply, session_id=session_id)
