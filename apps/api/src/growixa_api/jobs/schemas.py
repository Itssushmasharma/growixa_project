import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

# Shared job envelope per BACKGROUND_JOB_ARCHITECTURE.md — every job type (Sprint 1's
# healthcheck and every real business job from Slice 3 onward) is wrapped in this shape so
# consumers have one parsing/idempotency contract regardless of queue.
SYSTEM_HEALTHCHECK_QUEUE = "grx.system.healthcheck"


class JobEnvelope(BaseModel):
    job_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    idempotency_key: str
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    attempt_count: int = 0
    created_by_user_id: uuid.UUID | None = None
