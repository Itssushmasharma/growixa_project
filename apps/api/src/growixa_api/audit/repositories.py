import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.models import AuditLog


async def create_audit_log(
    session: AsyncSession,
    *,
    account_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    metadata: dict[str, Any],
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        account_id=account_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(audit_log)
    await session.flush()
    return audit_log


async def list_audit_logs(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[AuditLog]:
    stmt = (
        select(AuditLog)
        .where(AuditLog.account_id == account_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
