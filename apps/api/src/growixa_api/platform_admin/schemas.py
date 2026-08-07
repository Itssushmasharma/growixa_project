import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class AccountListItemOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    selected_plan_slug: str | None
    created_at: datetime
    user_count: int


class AccountUserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    status: str
    last_login_at: datetime | None


class SecurityEventOut(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    actor_user_id: uuid.UUID | None
    event_metadata: dict[str, Any]
    created_at: datetime


class AccountDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    selected_plan_slug: str | None
    created_at: datetime
    users: list[AccountUserOut]
    security_activity: list[SecurityEventOut]


class UpdateAccountStatusIn(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED", "CLOSED"]


class UsageSummaryItemOut(BaseModel):
    account_id: uuid.UUID
    account_name: str
    operation_type: str
    total_quantity: float
    unit: str


class CampaignOversightItemOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    account_name: str
    name: str
    status: str
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SupportSessionCreateIn(BaseModel):
    reason: str
    ticket_number: str
    access_level: Literal["READ", "WRITE"] = "READ"


class SupportSessionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    platform_admin_id: uuid.UUID
    reason: str
    ticket_number: str
    access_level: str
    started_at: datetime
    expires_at: datetime
    ended_at: datetime | None


class AuditEventOut(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    actor_user_id: uuid.UUID | None
    event_metadata: dict[str, Any]
    created_at: datetime


class SupportSessionContactOut(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    status: str


class SupportSessionCompanyOut(BaseModel):
    name: str
    website: str | None
    industry: str | None


class SupportSessionOverviewOut(BaseModel):
    session: SupportSessionOut
    company: SupportSessionCompanyOut | None
    contacts: list[SupportSessionContactOut]
    audit_events: list[AuditEventOut]


class SupportSessionContactUpdateIn(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
