import uuid
from typing import Literal

from pydantic import BaseModel


class RegisterIn(BaseModel):
    account_name: str
    full_name: str
    email: str
    password: str
    # Rejected at the API boundary (Pydantic) and the DB (CHECK) alike -- matches this
    # codebase's existing double-validation pattern for email_provider_connections.provider.
    plan_slug: Literal["starter", "growth"]


class RegisterOut(BaseModel):
    account_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    message: str
    # Populated only in local dev and the pytest suite -- no email-delivery channel
    # exists yet, same interim pattern as invitation tokens and password-reset tokens.
    token: str | None = None


class VerifyEmailIn(BaseModel):
    token: str
