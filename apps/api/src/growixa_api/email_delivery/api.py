import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.email_delivery.schemas import CampaignSendOut, TestSendIn
from growixa_api.email_delivery.services import (
    CampaignNotFoundError,
    CampaignNotSendableError,
    send_test_email,
    trigger_campaign_send,
)
from growixa_api.email_delivery.smtp_sender import EmailSendError
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

_require_send = require_permission("campaigns.send")


@router.post("/{campaign_id}/test-send", status_code=status.HTTP_204_NO_CONTENT)
async def test_send_route(
    campaign_id: uuid.UUID,
    payload: TestSendIn,
    _actor_id: uuid.UUID = Depends(_require_send),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await send_test_email(session, campaign_id, payload.to_email)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except EmailSendError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Test send failed: {exc}") from exc


@router.post(
    "/{campaign_id}/send", response_model=CampaignSendOut, status_code=status.HTTP_202_ACCEPTED
)
async def send_campaign_route(
    campaign_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_send),
    session: AsyncSession = Depends(get_session),
) -> CampaignSendOut:
    try:
        envelope = await trigger_campaign_send(session, campaign_id, actor_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except CampaignNotSendableError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Campaign is not in a sendable (DRAFT) state"
        ) from exc
    return CampaignSendOut(job_id=str(envelope.job_id))
