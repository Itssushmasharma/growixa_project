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
