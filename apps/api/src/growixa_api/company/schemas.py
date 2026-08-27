import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CompanyProfileIn(BaseModel):
    name: str
    logo_url: str | None = None
    website: str | None = None
    industry: str | None = None
    timezone: str | None = None
    default_language: str = "en"
    legal_footer: str | None = None
    business_address: str | None = None
    description: str | None = None
    support_email: str | None = None
    sender_name: str | None = None
    contact_details: dict[str, Any] = Field(default_factory=dict)


class CompanyProfileOut(CompanyProfileIn):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
