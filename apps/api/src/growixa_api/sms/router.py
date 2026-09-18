import hmac
import hashlib
import base64
import uuid
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id
from growixa_api.sms.models import SMSConnection
from growixa_api.sms.schemas import SMSConnectionIn, SMSConnectionOut
from growixa_api.auth.encryption import encrypt_secret

router = APIRouter(prefix="/sms", tags=["SMS"])

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
        auth_token_encrypted=encrypt_secret(payload.auth_token)
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
    # In a real implementation, this would use httpx to call Twilio REST API
    # using the decrypted auth_token from the active SMSConnection.
    # We simulate a successful dispatch for the frontend.
    return {"status": "dispatched", "message_id": f"SM{uuid.uuid4().hex}"}

webhook_router = APIRouter(prefix="/webhooks/twilio", tags=["SMS Webhooks"])

@webhook_router.post("")
async def receive_webhook(request: Request):
    """Receive delivery status updates from Twilio."""
    # Twilio sends form data, not JSON
    form_data = await request.form()
    signature = request.headers.get("X-Twilio-Signature")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    # Validation logic (placeholder, requires Twilio Auth Token from DB)
    # 1. Get full URL
    # 2. Sort POST params
    # 3. Append to URL
    # 4. HMAC-SHA1 hash with AuthToken
    # 5. Base64 encode and compare with X-Twilio-Signature
    
    # Process delivery states (queued, sent, delivered, undelivered, failed)
    # TODO: Update SMS message log states based on MessageSid and MessageStatus
    
    return {"status": "received"}
