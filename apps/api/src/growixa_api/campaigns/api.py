import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.campaigns.schemas import (
    CampaignIn,
    CampaignOut,
    CampaignUpdateIn,
    ScheduleCampaignIn,
)
from growixa_api.campaigns.services import (
    CampaignAlreadyScheduledError,
    CampaignNotCancellableError,
    CampaignNotEditableError,
    CampaignNotFoundError,
    InvalidRecipientTargetError,
    SenderIdentityNotFoundError,
    TemplateNotFoundError,
    cancel_campaign,
    create_campaign,
    get_campaign_or_raise,
    list_all_campaigns,
    schedule_campaign,
    update_campaign,
)
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

_require_manage = require_permission("campaigns.manage")
_require_view = require_permission("campaigns.view")


@router.get("", response_model=list[CampaignOut])
async def list_campaigns_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> list[CampaignOut]:
    campaigns = await list_all_campaigns(session)
    return [CampaignOut.model_validate(campaign) for campaign in campaigns]


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign_route(
    payload: CampaignIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> CampaignOut:
    try:
        campaign = await create_campaign(session, payload, actor_id)
    except SenderIdentityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender identity not found") from exc
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    except InvalidRecipientTargetError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    await session.commit()
    return CampaignOut.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign_route(
    campaign_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_view),
    session: AsyncSession = Depends(get_session),
) -> CampaignOut:
    try:
        campaign = await get_campaign_or_raise(session, campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    return CampaignOut.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign_route(
    campaign_id: uuid.UUID,
    payload: CampaignUpdateIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> CampaignOut:
    try:
        campaign = await update_campaign(session, campaign_id, payload)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except CampaignNotEditableError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Campaign is no longer a draft and cannot be edited"
        ) from exc
    except SenderIdentityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender identity not found") from exc
    except TemplateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found") from exc
    except InvalidRecipientTargetError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return CampaignOut.model_validate(campaign)


@router.post("/{campaign_id}/schedule", response_model=CampaignOut)
async def schedule_campaign_route(
    campaign_id: uuid.UUID,
    payload: ScheduleCampaignIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> CampaignOut:
    """Schedule a DRAFT campaign to be dispatched at a future datetime.

    Returns the updated campaign with status=SCHEDULED and scheduled_at set.
    """
    try:
        campaign = await schedule_campaign(session, campaign_id, payload)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except CampaignAlreadyScheduledError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Campaign cannot be scheduled in its current status",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return CampaignOut.model_validate(campaign)


@router.post("/{campaign_id}/cancel", response_model=CampaignOut)
async def cancel_campaign_route(
    campaign_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> CampaignOut:
    """Cancel a DRAFT or SCHEDULED campaign before it is dispatched.

    Returns the updated campaign with status=CANCELLED and cancelled_at set.
    """
    try:
        campaign = await cancel_campaign(session, campaign_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except CampaignNotCancellableError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Campaign cannot be cancelled in its current status",
        ) from exc
    return CampaignOut.model_validate(campaign)
