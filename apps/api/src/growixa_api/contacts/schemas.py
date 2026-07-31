import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CustomFieldIn(BaseModel):
    key: str
    label: str
    field_type: Literal["TEXT", "NUMBER", "DATE", "BOOLEAN"]


class CustomFieldOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    key: str
    label: str
    field_type: str


class ContactIn(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    source: str | None = None
    custom_fields: dict[str, str] = Field(default_factory=dict)


class ContactUpdateIn(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    custom_fields: dict[str, str] | None = None


class UpdateContactStatusIn(BaseModel):
    status: Literal["ACTIVE", "ARCHIVED"]


class ContactOut(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    status: str
    source: str | None
    created_at: datetime
    updated_at: datetime
    custom_fields: dict[str, str]
    tags: list[str] = Field(default_factory=list)
    is_suppressed: bool


class TagIn(BaseModel):
    name: str


class TagOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str


class AttachTagIn(BaseModel):
    tag_id: uuid.UUID


class ContactListIn(BaseModel):
    name: str
    description: str | None = None


class ContactListOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    member_count: int
    created_at: datetime
    updated_at: datetime


class AddListMemberIn(BaseModel):
    contact_id: uuid.UUID


class SegmentRuleIn(BaseModel):
    field: str
    operator: str
    value: str


class SegmentRuleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    field: str
    operator: str
    value: str


class SegmentIn(BaseModel):
    name: str
    type: Literal["DYNAMIC", "SAVED"]
    rules: list[SegmentRuleIn] = Field(default_factory=list)


class SegmentOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    member_count: int
    created_at: datetime
    updated_at: datetime
    rules: list[SegmentRuleOut]


class ContactImportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    filename: str
    status: str
    column_mapping: dict[str, str]
    total_rows: int
    imported_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    created_at: datetime
    completed_at: datetime | None


class ContactImportRowOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    row_number: int
    email: str | None
    status: str
    error_message: str | None


class ConsentRecordIn(BaseModel):
    channel: Literal["EMAIL", "SMS"]
    status: Literal["GRANTED", "WITHDRAWN", "UNKNOWN"]
    source: str | None = None


class ConsentRecordOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    channel: str
    status: str
    source: str | None
    recorded_at: datetime


class SuppressionEntryIn(BaseModel):
    email: str
    reason: Literal["UNSUBSCRIBED", "BOUNCED", "COMPLAINED", "MANUAL"]
    contact_id: uuid.UUID | None = None


class SuppressionEntryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    reason: str
    contact_id: uuid.UUID | None
    suppressed_at: datetime
