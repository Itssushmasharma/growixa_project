import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.audit.schemas import AuditLogOut
from growixa_api.audit.services import list_events
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/audit", tags=["audit"])

_require_view = require_permission("audit.view")


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs_route(
    entity_type: str | None = Query(default=None),
    actor_user_id: uuid.UUID | None = Query(default=None),
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLogOut]:
    events = await list_events(
        session, account_id=account_id, entity_type=entity_type, actor_user_id=actor_user_id
    )
    return [AuditLogOut.model_validate(event) for event in events]
