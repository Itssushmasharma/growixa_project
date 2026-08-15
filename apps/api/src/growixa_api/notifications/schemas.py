import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EmailProvider = Literal["POSTMARK", "CUSTOM_SMTP"]


class PlatformEmailProviderConfigIn(BaseModel):
    provider: EmailProvider
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    from_email: str
    from_name: str


class PlatformEmailProviderConfigOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: EmailProvider
    smtp_host: str
    smtp_port: int
    smtp_username: str
    from_email: str
    from_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Never the smtp_password or its encrypted form, in any response.
