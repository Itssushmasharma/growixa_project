import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ApprovalRequestCreate(BaseModel):
    entity_type: str = Field(..., pattern="^(EMAIL|SOCIAL)$")
    entity_id: uuid.UUID
    reviewer_id: uuid.UUID | None = None


class ApprovalRequestUpdate(BaseModel):
    status: str = Field(..., pattern="^(PENDING|APPROVED|REJECTED|CHANGES_REQUESTED)$")
    comments: str | None = None


class ApprovalRequestResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    requester_id: uuid.UUID
    reviewer_id: uuid.UUID | None
    status: str
    comments: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestListResponse(BaseModel):
    items: list[ApprovalRequestResponse]
    total: int
