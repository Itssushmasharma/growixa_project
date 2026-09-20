import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import RequirePermission, get_current_account_id
from growixa_api.sms.models import SMSConnection
from growixa_api.sms.schemas import SMSConnectionIn, SMSConnectionOut

router = APIRouter(
    prefix="/sms",
    tags=["SMS"],
    dependencies=[Depends(RequirePermission("integrations:manage"))],
)


@router.post("/connections", response_model=SMSConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_sms_connection(
    payload: SMSConnectionIn,
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SMSConnectionOut:
    conn = SMSConnection(
        account_id=account_id,
        provider=payload.provider,
        account_sid=payload.account_sid,
        sender_number=payload.sender_number,
        auth_token_encrypted=encrypt_secret(payload.auth_token),
    )
    session.add(conn)
    await session.commit()
    await session.refresh(conn)
    return SMSConnectionOut.model_validate(conn)


@router.get("/connections", response_model=list[SMSConnectionOut])
async def list_sms_connections(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[SMSConnectionOut]:
    result = await session.execute(
        select(SMSConnection).where(SMSConnection.account_id == account_id)
    )
    return [SMSConnectionOut.model_validate(c) for c in result.scalars().all()]


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_sms_message(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
):
    raise HTTPException(
        503,
        detail={
            "code": "FEATURE_PENDING",
            "message": "SMS delivery is pending provider integration. No message was sent.",
        },
    )


webhook_router = APIRouter(prefix="/webhooks/twilio", tags=["SMS Webhooks"])


@webhook_router.post("")
async def receive_webhook(request: Request) -> None:
    # Do not acknowledge events until signature verification and durable ingestion exist.
    raise HTTPException(503, detail="Webhook ingestion is pending provider integration")
