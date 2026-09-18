import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class CalendarEvent(BaseModel):
    id: uuid.UUID
    channel: str = Field(..., description="'EMAIL' or 'SOCIAL' or 'WHATSAPP' or 'SMS'")
    title: str
    status: str
    scheduled_at: datetime | None
    assignee_id: uuid.UUID | None = None

    class Config:
        from_attributes = True
