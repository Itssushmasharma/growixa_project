import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# GRX-EMAIL-011 / DEC-GRX-016: Postmark plus a generic Custom SMTP provider — no
# default, since a request omitting `provider` is now ambiguous rather than "obviously
# Postmark," and should 422 at the API boundary instead of silently picking one.
EmailProvider = Literal["POSTMARK", "CUSTOM_SMTP"]


class EmailProviderConnectionIn(BaseModel):
    provider: EmailProvider
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str


class EmailProviderConnectionTestIn(BaseModel):
    """No `provider` — connecting/authenticating over SMTP doesn't depend on which
    provider these credentials belong to. Used to validate a connection's fields before
    they're saved (or resaved)."""

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str


class EmailProviderConnectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: EmailProvider
    smtp_host: str
    smtp_port: int
    smtp_username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    webhook_username: str | None
    # Shown once, only in the response to the request that (re)generated it — never
    # persisted in plaintext, never returned by GET, per the same convention as
    # smtp_password. Populated by the API layer after creation, not model_validate.
    webhook_password: str | None = None


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
