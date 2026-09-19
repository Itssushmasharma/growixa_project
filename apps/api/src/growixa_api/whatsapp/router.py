import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from growixa_api.whatsapp.models import WhatsAppConnection
from growixa_api.whatsapp.schemas import WhatsAppConnectionIn, WhatsAppConnectionOut

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.post(
    "/connections", response_model=WhatsAppConnectionOut, status_code=status.HTTP_201_CREATED
)
async def create_whatsapp_connection(
    payload: WhatsAppConnectionIn,
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> WhatsAppConnectionOut:
    conn = WhatsAppConnection(
        account_id=account_id,
        waba_id=payload.waba_id,
        phone_number_id=payload.phone_number_id,
        access_token_encrypted=encrypt_secret(payload.access_token),
        webhook_verify_token_encrypted=encrypt_secret(payload.webhook_verify_token),
    )
    session.add(conn)
    await session.commit()
    await session.refresh(conn)
    return WhatsAppConnectionOut.model_validate(conn)


@router.get("/connections", response_model=list[WhatsAppConnectionOut])
async def list_whatsapp_connections(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[WhatsAppConnectionOut]:
    result = await session.execute(
        select(WhatsAppConnection).where(WhatsAppConnection.account_id == account_id)
    )
    return [WhatsAppConnectionOut.model_validate(c) for c in result.scalars().all()]


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_whatsapp_message(
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
):
    raise HTTPException(
        503,
        detail={
            "code": "FEATURE_PENDING",
            "message": "WHATSAPP delivery is pending provider integration. No message was sent.",
        },
    )


webhook_router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhooks"])


@webhook_router.get("")
async def verify_webhook(request: Request) -> None:
    raise HTTPException(503, detail="WhatsApp webhook verification is pending configuration")


@webhook_router.post("")
async def receive_webhook(request: Request) -> None:
    # Do not acknowledge events until signature verification and durable ingestion exist.
    raise HTTPException(503, detail="Webhook ingestion is pending provider integration")
