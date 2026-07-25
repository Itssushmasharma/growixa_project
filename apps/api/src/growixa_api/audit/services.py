import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.models import AuditLog
from growixa_api.audit.repositories import create_audit_log, list_audit_logs

# Defense in depth against T7 (secret leakage in logs): even if a caller accidentally
# includes one of these in an event's metadata, it never reaches the audit_logs row.
_SENSITIVE_METADATA_KEYS = {
    "password",
    "password_hash",
    "token",
    "token_hash",
    "refresh_token",
    "access_token",
    "secret",
}


def _redact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: ("[REDACTED]" if key.lower() in _SENSITIVE_METADATA_KEYS else value)
        for key, value in metadata.items()
    }


async def record_event(
    session: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    return await create_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=_redact_metadata(metadata or {}),
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def list_events(
    session: AsyncSession,
    *,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    limit: int = 100,
) -> Sequence[AuditLog]:
    return await list_audit_logs(
        session,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        limit=limit,
    )
