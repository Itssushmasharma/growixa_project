import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from growixa_api.approvals.models import ApprovalRequest


async def create_approval_request(
    session: AsyncSession,
    account_id: uuid.UUID,
    requester_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    reviewer_id: uuid.UUID | None = None,
) -> ApprovalRequest:
    approval = ApprovalRequest(
        account_id=account_id,
        entity_type=entity_type,
        entity_id=entity_id,
        requester_id=requester_id,
        reviewer_id=reviewer_id,
        status="PENDING",
    )
    session.add(approval)
    await session.flush()
    return approval


async def get_approval_request(
    session: AsyncSession, account_id: uuid.UUID, approval_id: uuid.UUID
) -> ApprovalRequest | None:
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.id == approval_id, ApprovalRequest.account_id == account_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_approval_requests(
    session: AsyncSession,
    account_id: uuid.UUID,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ApprovalRequest]:
    stmt = (
        select(ApprovalRequest)
        .where(ApprovalRequest.account_id == account_id)
        .order_by(ApprovalRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(ApprovalRequest.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_approval_status(
    session: AsyncSession,
    approval: ApprovalRequest,
    reviewer_id: uuid.UUID,
    status: str,
    comments: str | None = None,
) -> ApprovalRequest:
    approval.status = status
    approval.reviewer_id = reviewer_id
    if comments is not None:
        approval.comments = comments
    await session.flush()
    return approval
