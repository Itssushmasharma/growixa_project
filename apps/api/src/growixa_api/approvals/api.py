import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.approvals import services
from growixa_api.approvals.schemas import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalRequestUpdate,
    ApprovalRequestListResponse,
)
from growixa_api.permissions.dependencies import (
    get_current_account_id,
    get_current_user_id,
    require_permission,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post(
    "",
    response_model=ApprovalRequestResponse,
    dependencies=[Depends(require_permission("client.approve"))],
)
async def create_approval(
    data: ApprovalRequestCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
):
    return await services.create_approval_request(
        session, account_id, user_id, data
    )


@router.get(
    "/{approval_id}",
    response_model=ApprovalRequestResponse,
    dependencies=[Depends(require_permission("client.view"))],
)
async def get_approval(
    approval_id: uuid.UUID,
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
):
    return await services.get_approval_request(session, account_id, approval_id)


@router.get(
    "",
    response_model=ApprovalRequestListResponse,
    dependencies=[Depends(require_permission("client.view"))],
)
async def list_approvals(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
):
    items = await services.list_approval_requests(
        session, account_id, status=status, limit=limit, offset=offset
    )
    return {"items": items, "total": len(items)}


@router.patch(
    "/{approval_id}/status",
    response_model=ApprovalRequestResponse,
    dependencies=[Depends(require_permission("client.approve"))],
)
async def update_approval_status(
    approval_id: uuid.UUID,
    data: ApprovalRequestUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
):
    return await services.update_approval_status(
        session, account_id, approval_id, user_id, data
    )
