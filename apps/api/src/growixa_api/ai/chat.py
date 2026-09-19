"""Public assistant availability; metered tenant AI remains in ai.api."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["ai-chat"])


class ChatMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)


class ChatMessageOut(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatMessageOut)
async def ai_chat_route(payload: ChatMessageIn) -> ChatMessageOut:
    """Fail closed until public chat has abuse controls and a metered provider path."""
    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "FEATURE_PENDING",
            "message": "Public AI chat is unavailable. Use the authenticated AI workspace.",
        },
    )
