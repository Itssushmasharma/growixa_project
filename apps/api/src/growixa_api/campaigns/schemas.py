import uuid
from datetime import datetime

from pydantic import BaseModel


class CampaignIn(BaseModel):
    name: str
    subject: str
    body_html: str
    body_text: str | None = None
    template_id: uuid.UUID | None = None
    sender_identity_id: uuid.UUID
    recipient_type: str
    recipient_segment_id: uuid.UUID | None = None
    recipient_list_id: uuid.UUID | None = None


class CampaignUpdateIn(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    template_id: uuid.UUID | None = None
    sender_identity_id: uuid.UUID | None = None
    recipient_type: str | None = None
    recipient_segment_id: uuid.UUID | None = None
    recipient_list_id: uuid.UUID | None = None


class ScheduleCampaignIn(BaseModel):
    """Body for POST /campaigns/{id}/schedule."""

    scheduled_at: datetime
    """UTC datetime for when to dispatch this campaign. Must be in the future."""


class CampaignOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    subject: str
    body_html: str
    body_text: str | None
    template_id: uuid.UUID | None
    sender_identity_id: uuid.UUID
    recipient_type: str
    recipient_segment_id: uuid.UUID | None
    recipient_list_id: uuid.UUID | None
    status: str
    scheduled_at: datetime | None
    cancelled_at: datetime | None
    idempotency_key: uuid.UUID
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None
    sent_count: int | None = None
    delivered_count: int | None = None
    opened_count: int | None = None
    clicked_count: int | None = None
    total_opened_count: int | None = None
    total_clicked_count: int | None = None
    open_rate_pct: float | None = None
    click_rate_pct: float | None = None
    click_to_open_rate_pct: float | None = None
