import uuid
from datetime import datetime

from pydantic import BaseModel


class InviteUserIn(BaseModel):
    email: str
    role_name: str


class InviteUserOut(BaseModel):
    id: uuid.UUID
    email: str
    expires_at: datetime
    # Sprint 1 has no email-delivery channel yet (see AGENT_HANDOFF.md's GRX-USER-001
    # entry) — the raw token is returned here so an admin can pass it to the invitee
    # out-of-band. Revisit once notifications/email delivery exists.
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
