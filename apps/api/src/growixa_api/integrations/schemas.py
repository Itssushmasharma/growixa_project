import uuid
from datetime import datetime

from pydantic import BaseModel


class EmailProviderConnectionIn(BaseModel):
    provider: str = "POSTMARK"
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str


class EmailProviderConnectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SenderIdentityIn(BaseModel):
    email_provider_connection_id: uuid.UUID
    from_email: str
    from_name: str
    reply_to_email: str | None = None


class SenderIdentityStatusIn(BaseModel):
    verification_status: str


class SenderIdentityOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email_provider_connection_id: uuid.UUID
    from_email: str
    from_name: str
    reply_to_email: str | None
    verification_status: str
    created_at: datetime
    updated_at: datetime
