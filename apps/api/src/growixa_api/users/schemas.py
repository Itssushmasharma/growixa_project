import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class InviteUserIn(BaseModel):
    email: str
    role_name: str


class InviteUserOut(BaseModel):
    id: uuid.UUID
    email: str
    expires_at: datetime
    # The invitee is emailed an accept link (GRX-USER-003), but that send is best-effort
    # — it is skipped entirely when no platform email provider is configured, and a relay
    # failure is only logged. The raw token stays in the response so the inviting admin
    # always retains the out-of-band fallback rather than losing the invitation to a
    # silent send failure.
    token: str


class AcceptInvitationIn(BaseModel):
    token: str
    password: str
    full_name: str


class AcceptInvitationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str


class UserListItemOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    status: str
    last_login_at: datetime | None
    roles: list[str]


class UpdateUserStatusIn(BaseModel):
    status: Literal["ACTIVE", "DISABLED"]


class UpdateUserRoleIn(BaseModel):
    role_name: str
