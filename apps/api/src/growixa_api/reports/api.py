import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from growixa_api.reports.models import ScheduledReport

router = APIRouter(prefix="/reports", tags=["White-label Reports"])

class CreateReportReq(BaseModel):
    name: str
    frequency: str
    report_type: str
    recipient_emails: list[str]

@router.get("/")
async def list_reports(
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(ScheduledReport)
        .where(ScheduledReport.account_id == account_id)
        .order_by(ScheduledReport.created_at.desc())
    )
    return result.scalars().all()

@router.post("/")
async def create_report(
    payload: CreateReportReq,
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    report = ScheduledReport(
        account_id=account_id,
        name=payload.name,
        frequency=payload.frequency,
        report_type=payload.report_type,
        recipient_emails=payload.recipient_emails
    )
    session.add(report)
    await session.commit()
    return report
