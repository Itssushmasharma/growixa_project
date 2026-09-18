import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Custom Fields
# ---------------------------------------------------------------------------


class CustomFieldIn(BaseModel):
    key: str
    label: str
    field_type: Literal["TEXT", "NUMBER", "DATE", "BOOLEAN"]
    is_personalization_usable: bool = True


class CustomFieldOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    key: str
    label: str
    field_type: str
    is_personalization_usable: bool


# ---------------------------------------------------------------------------
# CRM Companies
# ---------------------------------------------------------------------------


class CompanyIn(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    address: str | None = None
    lifecycle_stage: Literal[
        "PROSPECT", "LEAD", "QUALIFIED", "CUSTOMER", "CHURNED", "PARTNER", "OTHER"
    ] = "PROSPECT"
    custom_attributes: dict = Field(default_factory=dict)


class CompanyUpdateIn(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    address: str | None = None
    lifecycle_stage: (
        Literal["PROSPECT", "LEAD", "QUALIFIED", "CUSTOMER", "CHURNED", "PARTNER", "OTHER"] | None
    ) = None
    custom_attributes: dict | None = None


class CompanyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    domain: str | None = None
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    address: str | None = None
    lifecycle_stage: str
    custom_attributes: dict = Field(default_factory=dict)
    contacts_count: int = 0
    created_at: datetime
    updated_at: datetime


class CompanyListOut(BaseModel):
    items: list[CompanyOut]
    total: int


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


class ContactIn(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company_id: uuid.UUID | None = None
    job_title: str | None = None
    lifecycle_stage: Literal[
        "SUBSCRIBER", "LEAD", "MQL", "SQL", "OPPORTUNITY", "CUSTOMER", "EVANGELIST", "OTHER"
    ] = "LEAD"
    source: str | None = None
    custom_fields: dict[str, str] = Field(default_factory=dict)
    custom_attributes: dict = Field(default_factory=dict)


class ContactUpdateIn(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company_id: uuid.UUID | None = None
    job_title: str | None = None
    lifecycle_stage: (
        Literal[
            "SUBSCRIBER", "LEAD", "MQL", "SQL", "OPPORTUNITY", "CUSTOMER", "EVANGELIST", "OTHER"
        ]
        | None
    ) = None
    status: Literal["ACTIVE", "ARCHIVED"] | None = None
    source: str | None = None
    custom_fields: dict[str, str] | None = None
    custom_attributes: dict | None = None


class UpdateContactStatusIn(BaseModel):
    status: Literal["ACTIVE", "ARCHIVED"]


class ContactStatsOut(BaseModel):
    """Account-wide contact status counts -- feeds the Contacts page's stat badges."""

    total: int
    active: int
    archived: int
    suppressed: int
    new_this_month: int


class ContactCountOut(BaseModel):
    """Total contacts matching current filters."""

    total: int


class ContactOut(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    company_id: uuid.UUID | None = None
    company_name: str | None = None
    job_title: str | None = None
    lifecycle_stage: str = "LEAD"
    status: str
    source: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    custom_fields: dict[str, str]
    custom_attributes: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    is_suppressed: bool


# ---------------------------------------------------------------------------
# Contact Activities
# ---------------------------------------------------------------------------


class ContactActivityIn(BaseModel):
    model_config = {"populate_by_name": True}

    activity_type: Literal[
        "NOTE",
        "STAGE_CHANGE",
        "TAG_ADDED",
        "TAG_REMOVED",
        "EMAIL_SENT",
        "EMAIL_OPENED",
        "IMPORT",
        "CONSENT_CHANGE",
        "TASK",
        "CALL",
    ] = "NOTE"
    title: str
    description: str | None = None
    metadata_: dict = Field(default_factory=dict, alias="metadata")

    @property
    def metadata(self) -> dict:
        return self.metadata_


class ContactActivityOut(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: uuid.UUID
    contact_id: uuid.UUID
    activity_type: str
    title: str
    description: str | None = None
    metadata_: dict = Field(default_factory=dict, alias="metadata", validation_alias="metadata_")
    created_by_user_id: uuid.UUID | None = None
    created_at: datetime


class ContactActivityListOut(BaseModel):
    items: list[ContactActivityOut]
    total: int


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class TagIn(BaseModel):
    name: str


class TagUpdateIn(BaseModel):
    name: str


class TagOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    contacts_count: int = 0


class AttachTagIn(BaseModel):
    tag_id: uuid.UUID


class BulkTagIn(BaseModel):
    contact_ids: list[uuid.UUID]
    tag_id: uuid.UUID | None = None
    tag_name: str | None = None
    action: Literal["ATTACH", "DETACH"] = "ATTACH"


class BulkTagOut(BaseModel):
    affected: int
    tag_id: uuid.UUID | None = None
    tag_name: str | None = None
    action: str


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------


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
    match_type: Literal["ALL", "ANY"] = "ALL"
    rules: list[SegmentRuleIn] = Field(default_factory=list)


class SegmentUpdateIn(BaseModel):
    name: str | None = None
    type: Literal["DYNAMIC", "SAVED"] | None = None
    match_type: Literal["ALL", "ANY"] | None = None
    rules: list[SegmentRuleIn] | None = None


class SegmentOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    match_type: str = "ALL"
    member_count: int
    created_at: datetime
    updated_at: datetime
    rules: list[SegmentRuleOut]


class SegmentPreviewIn(BaseModel):
    match_type: Literal["ALL", "ANY"] = "ALL"
    rules: list[SegmentRuleIn] = Field(default_factory=list)


class SegmentPreviewOut(BaseModel):
    count: int


class SegmentSnapshotOut(BaseModel):
    segment_id: uuid.UUID
    frozen_member_count: int


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


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


class CSVDetectOut(BaseModel):
    headers: list[str]
    sample_rows: list[list[str]]
    suggested_mapping: dict[str, str | None]
    total_rows_estimate: int


# ---------------------------------------------------------------------------
# Consent & Suppression
# ---------------------------------------------------------------------------


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


class DomainSuppressionIn(BaseModel):
    domain: str


class PhoneSuppressionIn(BaseModel):
    phone: str
    reason: Literal["UNSUBSCRIBED", "BOUNCED", "COMPLAINED", "MANUAL"] = "MANUAL"


class SuppressionEntryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str | None
    domain: str | None
    phone: str | None = None
    reason: str
    contact_id: uuid.UUID | None
    suppressed_at: datetime


class SuppressionImportResultOut(BaseModel):
    created: int
    skipped: int
    total_rows: int


# ---------------------------------------------------------------------------
# Bulk Operations
# ---------------------------------------------------------------------------


class BulkDeleteContactsIn(BaseModel):
    contact_ids: list[uuid.UUID]


class BulkDeleteContactsOut(BaseModel):
    deleted_count: int


class BulkRestoreContactsIn(BaseModel):
    contact_ids: list[uuid.UUID]


class BulkRestoreContactsOut(BaseModel):
    restored_count: int
