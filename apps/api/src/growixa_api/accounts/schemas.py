import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RegisterIn(BaseModel):
    account_name: str
    full_name: str
    email: str
    password: str
    # Rejected at the API boundary (Pydantic) and the DB (CHECK) alike -- matches this
    # codebase's existing double-validation pattern for email_provider_connections.provider.
    # Recorded only, a UX intent signal -- real entitlement is always Free at
    # registration regardless of this value (GRX-BILL-002). No "enterprise" option:
    # that tier is contact-sales, never self-serve at registration (DEC-GRX-030).
    plan_slug: Literal["free", "starter", "pro"]


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


class SupportSessionStatusOut(BaseModel):
    """GRX-SAAS-010 / DEC-GRX-022 point 6 -- the only place a support session's
    existence is visible from the customer side. Deliberately no support_session_id or
    platform_admin identity here: this is a presence check for the banner, not a way
    for a customer to enumerate platform-admin activity."""

    active: bool
    started_at: datetime | None
    reason: str | None
