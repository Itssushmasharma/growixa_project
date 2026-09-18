import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChannelCapabilityOut(BaseModel):
    model_config = {"from_attributes": True}

    provider_name: str
    display_name: str
    max_characters: int
    supported_media_types: list[str] = ["IMAGE"]
    max_media_count: int = 1
    requires_media: bool = False
    supports_video: bool = False
    supports_scheduling: bool = True
    is_configured: bool = True
    setup_guide: str | None = None


class SocialConnectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: str
    provider_account_id: str | None = None
    provider_username: str | None = None
    provider_account_name: str | None = None
    ig_business_account_id: str | None = None
    ig_username: str | None = None
    facebook_page_id: str | None = None
    is_active: bool
    last_connected_at: datetime
    last_error: str | None = None
    token_expires_at: datetime | None = None


class SocialPostMediaOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    media_type: str
    public_url: str
    position: int
    file_size_bytes: int | None = None
    mime_type: str | None = None


class SocialPostIn(BaseModel):
    social_connection_id: uuid.UUID
    caption: str = ""
    campaign_id: uuid.UUID | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None


class SocialPostUpdateIn(BaseModel):
    caption: str | None = None
    campaign_id: uuid.UUID | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None


class ScheduleSocialPostIn(BaseModel):
    """Body for POST /social/posts/{id}/schedule."""

    scheduled_at: datetime
    """UTC datetime for when to dispatch this post. Must be in the future."""


class SocialPostOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    social_connection_id: uuid.UUID
    caption: str
    status: str
    scheduled_at: datetime | None = None
    cancelled_at: datetime | None = None
    published_at: datetime | None = None
    campaign_id: uuid.UUID | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    ig_media_id: str | None = None
    ig_permalink: str | None = None
    provider_post_id: str | None = None
    provider_permalink: str | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    media: list[SocialPostMediaOut] = []


class SocialPostJobOut(BaseModel):
    job_id: str


class BulkScheduleItemIn(BaseModel):
    social_connection_id: uuid.UUID
    caption: str = ""
    scheduled_at: datetime
    media_items: list[dict[str, object]] = Field(default_factory=list)
    campaign_id: uuid.UUID | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None


class BulkScheduleIn(BaseModel):
    items: list[BulkScheduleItemIn] = Field(min_length=1, max_length=50)
    stagger_interval_minutes: int = Field(default=15, ge=1, le=120)


class BulkScheduleOut(BaseModel):
    total_requested: int
    scheduled_count: int
    failed_count: int
    scheduled_posts: list[uuid.UUID]
    errors: list[dict[str, str]]
