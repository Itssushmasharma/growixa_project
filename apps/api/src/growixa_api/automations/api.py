import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from growixa_api.automations.models import Workflow
from growixa_api.automations.schemas import WorkflowIn, WorkflowOut
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id

router = APIRouter(prefix="/automations", tags=["automations"])

@router.get("", response_model=list[WorkflowOut])
async def list_workflows_route(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[WorkflowOut]:
    result = await session.execute(
        select(Workflow).where(Workflow.account_id == account_id).order_by(Workflow.created_at.desc())
    )
    return [WorkflowOut.model_validate(w) for w in result.scalars().all()]

@router.post("", response_model=WorkflowOut, status_code=status.HTTP_201_CREATED)
async def create_workflow_route(
    payload: WorkflowIn,
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> WorkflowOut:
    workflow = Workflow(
        account_id=account_id,
        name=payload.name,
        description=payload.description,
        trigger_type=payload.trigger_type,
        conditions=[c.model_dump() for c in payload.conditions],
        actions=[a.model_dump() for a in payload.actions]
    )
    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return WorkflowOut.model_validate(workflow)
