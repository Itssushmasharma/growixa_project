import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.schemas import AuditLogOut
from growixa_api.audit.services import list_events
from growixa_api.db import get_session
from growixa_api.pagination import DEFAULT_LIMIT, clamp_limit
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/audit", tags=["audit"])

_require_view = require_permission("audit.view")


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs_route(
    entity_type: str | None = Query(default=None),
    actor_user_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1),
    offset: int = Query(default=0, ge=0),
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLogOut]:
    events = await list_events(
        session,
        account_id=account_id,
        entity_type=entity_type,
        actor_user_id=actor_user_id,
        limit=clamp_limit(limit),
        offset=offset,
    )
    return [AuditLogOut.model_validate(event) for event in events]
