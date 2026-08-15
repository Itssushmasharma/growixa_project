import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.email_delivery.schemas import (
    CampaignSendOut,
    PostmarkWebhookPayload,
    TestSendIn,
)
from growixa_api.email_delivery.services import (
    CampaignNotFoundError,
    CampaignNotSendableError,
    CampaignRecipientNotFoundError,
    record_unsubscribe,
    record_webhook_event,
    send_test_email,
    trigger_campaign_send,
    verify_webhook_credentials,
)
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
public_router = APIRouter(tags=["email-delivery-public"])

_require_send = require_permission("campaigns.send")
_basic_auth = HTTPBasic()


@router.post("/{campaign_id}/test-send", status_code=status.HTTP_204_NO_CONTENT)
async def test_send_route(
    campaign_id: uuid.UUID,
    payload: TestSendIn,
    _actor_id: uuid.UUID = Depends(_require_send),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await send_test_email(session, account_id, campaign_id, payload.to_email)
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
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> CampaignSendOut:
    try:
        envelope = await trigger_campaign_send(session, account_id, campaign_id, actor_id)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found") from exc
    except CampaignNotSendableError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Campaign is not in a sendable (DRAFT) state"
        ) from exc
    return CampaignSendOut(job_id=str(envelope.job_id))


@public_router.post("/webhooks/postmark", status_code=status.HTTP_200_OK)
async def postmark_webhook_route(
    payload: PostmarkWebhookPayload,
    credentials: HTTPBasicCredentials = Depends(_basic_auth),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Public per THREAT_MODEL.md's T14 — authenticated via HTTP Basic Auth (checked
    against every account's active connection's own webhook credentials, since this
    route carries no account identifier of its own) instead of a user session, since
    Postmark itself is the caller. A failed check is rejected before this function ever
    touches `email_events`/`message_deliveries`, per SPRINT_03's acceptance criteria."""
    account_id = await verify_webhook_credentials(
        session, credentials.username, credentials.password
    )
    if account_id is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid webhook credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    await record_webhook_event(session, account_id, payload)
    return {"status": "ok"}


@public_router.get("/unsubscribe/{campaign_recipient_id}", response_class=Response)
async def unsubscribe_route(
    campaign_recipient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Fully public and unauthenticated by design — this is the link a recipient clicks
    from their email client, identified only by the unguessable `campaign_recipient_id`
    UUID (same security shape as the invitation-accept token)."""
    try:
        await record_unsubscribe(session, campaign_recipient_id)
    except CampaignRecipientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unsubscribe link not found") from exc
    return Response(
        content="<html><body><p>You have been unsubscribed.</p></body></html>",
        media_type="text/html",
    )


@public_router.post("/unsubscribe/{campaign_recipient_id}", status_code=status.HTTP_200_OK)
async def one_click_unsubscribe_route(
    campaign_recipient_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """RFC 8058 one-click unsubscribe -- the same public/unauthenticated shape as the GET
    route above, but the mail client itself (not the recipient's browser) issues this POST
    directly, in response to the campaign send's `List-Unsubscribe-Post` header. No HTML
    body: per RFC 8058, the response is consumed by the mail client, never rendered."""
    try:
        await record_unsubscribe(session, campaign_recipient_id)
    except CampaignRecipientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unsubscribe link not found") from exc
    return Response(status_code=status.HTTP_200_OK)
