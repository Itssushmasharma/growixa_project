import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BrandProfileIn(BaseModel):
    brand_voice: str | None = None
    forbidden_claims: list[Any] = Field(default_factory=list)
    required_facts: list[Any] = Field(default_factory=list)


class BrandProfileOut(BrandProfileIn):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
