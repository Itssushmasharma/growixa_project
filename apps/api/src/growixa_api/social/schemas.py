import uuid
from datetime import datetime

from pydantic import BaseModel


class SocialConnectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: str
    ig_business_account_id: str
    ig_username: str | None
    facebook_page_id: str
    is_active: bool
    last_connected_at: datetime
    last_error: str | None


class SocialPostMediaOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    media_type: str
    public_url: str
    position: int


class SocialPostIn(BaseModel):
    social_connection_id: uuid.UUID
    caption: str = ""


class SocialPostUpdateIn(BaseModel):
    caption: str | None = None


class SocialPostOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    social_connection_id: uuid.UUID
    caption: str
    status: str
    scheduled_at: datetime | None
    cancelled_at: datetime | None
    published_at: datetime | None
    ig_media_id: str | None
    ig_permalink: str | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    media: list[SocialPostMediaOut] = []
