import uuid
from datetime import datetime

from pydantic import BaseModel


class EmailTemplateVersionIn(BaseModel):
    subject: str
    body_html: str
    body_text: str | None = None


class EmailTemplateIn(EmailTemplateVersionIn):
    name: str


class EmailTemplateVersionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    template_id: uuid.UUID
    version_number: int
    subject: str
    body_html: str
    body_text: str | None
    created_at: datetime


class EmailTemplateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    is_platform_default: bool
    created_at: datetime
    updated_at: datetime
    current_version: EmailTemplateVersionOut | None


class TemplateValidationIn(BaseModel):
    subject: str
    body_html: str
    body_text: str | None = None


class TemplateValidationOut(BaseModel):
    valid: bool
    warnings: list[str] = []
