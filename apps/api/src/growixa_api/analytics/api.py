import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.analytics.schemas import CampaignReportOut
from growixa_api.analytics.services import CampaignNotFoundError, get_campaign_report
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/campaigns", tags=["analytics"])

_require_view = require_permission("campaigns.view")


@router.get("/{campaign_id}/report", response_model=CampaignReportOut)
async def get_campaign_report_route(
    campaign_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> CampaignReportOut:
    try:
        report = await get_campaign_report(session, account_id, campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    return CampaignReportOut.model_validate(report)
