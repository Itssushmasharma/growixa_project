import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class AuditLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    event_metadata: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    # Postgres INET comes back from asyncpg as an ipaddress.IPv4Address/IPv6Address
    # object, not a str — stringify it here rather than widening the field's type,
    # since every consumer (JSON API, frontend) just wants the address as text.
    @field_validator("ip_address", mode="before")
    @classmethod
    def _stringify_ip_address(cls, value: object) -> object:
        return value if value is None or isinstance(value, str) else str(value)
