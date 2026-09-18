import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.analytics.schemas import (
    CampaignComparisonOut,
    CampaignReportOut,
    CampaignTimeseriesOut,
)
from growixa_api.analytics.services import (
    CampaignNotFoundError,
    export_campaign_csv,
    get_campaign_comparison,
    get_campaign_report,
    get_campaign_timeseries,
)
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


@router.get("/{campaign_id}/analytics/timeseries", response_model=CampaignTimeseriesOut)
async def get_campaign_timeseries_route(
    campaign_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> CampaignTimeseriesOut:
    """Returns hour-by-hour event delivery and engagement timeline for the campaign."""
    try:
        ts = await get_campaign_timeseries(session, account_id, campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    return CampaignTimeseriesOut.model_validate(ts)


@router.get("/{campaign_id}/analytics/comparison", response_model=CampaignComparisonOut)
async def get_campaign_comparison_route(
    campaign_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> CampaignComparisonOut:
    """Returns campaign engagement rates compared to the account average."""
    try:
        comparison = await get_campaign_comparison(session, account_id, campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    return CampaignComparisonOut.model_validate(comparison)


@router.get("/{campaign_id}/analytics/export")
async def export_campaign_analytics_route(
    campaign_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Exports CSV log of all recipients with their delivery, open, and bounce statuses."""
    try:
        csv_content = await export_campaign_csv(session, account_id, campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=campaign_{campaign_id}_recipients.csv"
        },
    )
