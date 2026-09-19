from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from growixa_api.db import get_session
from growixa_api.config import get_settings
import httpx

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
    
    settings = get_settings()
    
    if not settings.openai_api_key:
        # Fallback dummy responses if no key is configured
        if "pricing" in user_msg or "cost" in user_msg:
            reply = "Our pricing starts at $49/mo for the Pro plan. You can check out more details on our pricing page!"
        elif "contact" in user_msg or "support" in user_msg:
            reply = "You can reach our support team at support@growixa.com."
        elif "hi" in user_msg or "hello" in user_msg:
            reply = "Hello! I am Growixa AI. How can I help you grow your business today?"
        else:
            reply = "I'm still learning! But I can help you navigate our marketing OS. Could you rephrase your question?"
    else:
        # Call OpenAI directly via REST
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "You are Growixa AI, a helpful assistant for a marketing automation platform. Keep your answers concise, professional, and friendly."},
                            {"role": "user", "content": payload.message}
                        ],
                        "max_tokens": 150
                    }
                )
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"I'm sorry, I'm having trouble connecting to my AI brain right now. ({str(e)})"

    return ChatMessageOut(reply=reply, session_id=session_id)
