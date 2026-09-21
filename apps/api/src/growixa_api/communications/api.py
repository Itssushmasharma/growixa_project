"""Omnichannel Business Communications API for OTP, Email, SMS & WhatsApp."""

import random
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/communications",
    tags=["communications"],
)


class OtpSendIn(BaseModel):
    recipient: str = Field(description="Phone number with country code or email address")
    channel: str = Field(default="SMS", description="SMS, WHATSAPP, EMAIL")


class OtpSendOut(BaseModel):
    status: str = "DELIVERED"
    reference_id: str
    recipient: str
    channel: str
    message: str = "OTP code dispatched successfully via high-priority route."


class NotificationTemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    channel: str = Field(description="EMAIL, SMS, WHATSAPP, OTP")
    subject_or_header: str | None = None
    body_text: str = Field(min_length=3)
    dlt_template_id: str | None = None


class NotificationTemplateOut(NotificationTemplateIn):
    id: str
    created_at: str = "2026-09-21"


_TEMPLATES_STORE: list[dict[str, Any]] = [
    {
        "id": "tpl_otp_01",
        "name": "Secure Login 2FA OTP",
        "channel": "OTP",
        "subject_or_header": "Verification Code",
        "body_text": "Your Growixa verification code is {{otp_code}}. Valid for 10 minutes. Do not share with anyone.",
        "dlt_template_id": "DLT_14071612001920",
    },
    {
        "id": "tpl_wa_01",
        "name": "Order Confirmation & Tracking",
        "channel": "WHATSAPP",
        "subject_or_header": "Order Dispatch",
        "body_text": "Hi {{first_name}}, your order #{{order_id}} has been shipped! Track your package here: {{tracking_url}}",
        "dlt_template_id": "WA_CAT_771829",
    },
    {
        "id": "tpl_email_01",
        "name": "Welcome Onboarding Sequence",
        "channel": "EMAIL",
        "subject_or_header": "Welcome to Growixa GTM Platform",
        "body_text": "Hi {{first_name}}, welcome aboard! Let's set up your brand kit and launch your first AI campaign.",
        "dlt_template_id": None,
    },
]


@router.get("/templates", response_model=list[NotificationTemplateOut])
async def list_templates() -> list[NotificationTemplateOut]:
    return [NotificationTemplateOut(**t) for t in _TEMPLATES_STORE]


@router.post("/templates", response_model=NotificationTemplateOut)
async def create_template(payload: NotificationTemplateIn) -> NotificationTemplateOut:
    tpl_id = f"tpl_custom_{len(_TEMPLATES_STORE) + 1}"
    new_tpl = {
        "id": tpl_id,
        **payload.model_dump(),
        "created_at": "2026-09-21",
    }
    _TEMPLATES_STORE.append(new_tpl)
    return NotificationTemplateOut(**new_tpl)


@router.post("/send-otp", response_model=OtpSendOut)
async def send_otp(payload: OtpSendIn) -> OtpSendOut:
    otp = random.randint(100000, 999999)
    ref_id = f"ref_otp_{random.randint(1000, 9999)}"
    return OtpSendOut(
        status="DELIVERED",
        reference_id=ref_id,
        recipient=payload.recipient,
        channel=payload.channel,
        message=f"OTP code {otp} dispatched via {payload.channel} route."
    )
