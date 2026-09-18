import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from growixa_api.approvals import repositories
from growixa_api.approvals.models import ApprovalRequest
from growixa_api.approvals.schemas import ApprovalRequestCreate, ApprovalRequestUpdate


async def create_approval_request(
    session: AsyncSession,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ApprovalRequestCreate,
) -> ApprovalRequest:
    # Here we would typically validate that the entity_id exists and the user has access.
    # We will assume that check is done by the caller (e.g. CampaignService).
    return await repositories.create_approval_request(
        session=session,
        account_id=account_id,
        requester_id=user_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        reviewer_id=data.reviewer_id,
    )


async def get_approval_request(
    session: AsyncSession, account_id: uuid.UUID, approval_id: uuid.UUID
) -> ApprovalRequest:
    approval = await repositories.get_approval_request(session, account_id, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval


async def list_approval_requests(
    session: AsyncSession,
    account_id: uuid.UUID,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ApprovalRequest]:
    return await repositories.list_approval_requests(
        session=session,
        account_id=account_id,
        status=status,
        limit=limit,
        offset=offset,
    )


async def update_approval_status(
    session: AsyncSession,
    account_id: uuid.UUID,
    approval_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ApprovalRequestUpdate,
) -> ApprovalRequest:
    approval = await get_approval_request(session, account_id, approval_id)
    
    # State machine transition enforcement
    if approval.status in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400, 
            detail=f"Approval request is already in terminal state: {approval.status}"
        )
        
    updated = await repositories.update_approval_status(
        session=session,
        approval=approval,
        reviewer_id=user_id,
        status=data.status,
        comments=data.comments,
    )
    
    # TODO: Once approved, trigger downstream scheduling via RabbitMQ if it was a scheduled campaign
    
    return updated
