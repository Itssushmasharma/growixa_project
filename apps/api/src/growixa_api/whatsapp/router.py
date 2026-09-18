import hmac
import hashlib
import uuid
from fastapi import APIRouter, Request, HTTPException, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from growixa_api.whatsapp.models import WhatsAppConnection
from growixa_api.whatsapp.schemas import WhatsAppConnectionIn, WhatsAppConnectionOut
from growixa_api.auth.encryption import encrypt_secret

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

@router.post("/connections", response_model=WhatsAppConnectionOut, status_code=status.HTTP_201_CREATED)
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
        webhook_verify_token_encrypted=encrypt_secret(payload.webhook_verify_token)
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
    # In a real implementation, this would use httpx to call Meta's Graph API
    # using the decrypted access_token from the active WhatsAppConnection.
    # We simulate a successful dispatch for the frontend.
    return {"status": "dispatched", "message_id": f"wamid.{uuid.uuid4().hex}"}

webhook_router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhooks"])

@webhook_router.get("")
async def verify_webhook(request: Request):
    """Meta Cloud API webhook verification step."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # In production, query the DB to find a connection matching the verify_token
    # For now, we simulate success if mode is subscribe
    if mode == "subscribe" and token and challenge:
        return Response(content=challenge, media_type="text/plain")
        
    raise HTTPException(status_code=403, detail="Verification failed")

@webhook_router.post("")
async def receive_webhook(request: Request):
    """Receive status updates and inbound messages from WhatsApp."""
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    # Validation logic (placeholder, requires App Secret from DB)
    # expected_signature = "sha256=" + hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
    # if not hmac.compare_digest(signature, expected_signature):
    #     raise HTTPException(status_code=401, detail="Invalid signature")
        
    data = await request.json()
    
    # Process statuses (sent, delivered, read, failed)
    # TODO: Update WhatsApp message log states based on data
    
    return {"status": "received"}
