import uuid

from pydantic import BaseModel


class LoginIn(BaseModel):
    email: str
    password: str


class LoginOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str


class PasswordResetRequestIn(BaseModel):
    email: str


class PasswordResetRequestOut(BaseModel):
    message: str
    # Populated only when `settings.environment == "local"` — there is no email-delivery
    # channel yet (see GRX-USER-001's invitation-token handoff for the same interim
    # pattern). Must stay `None` in any non-local environment; see THREAT_MODEL.md T11.
    token: str | None = None


class PasswordResetCompleteIn(BaseModel):
    token: str
    new_password: str
