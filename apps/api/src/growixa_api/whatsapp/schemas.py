import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional

class WhatsAppConnectionIn(BaseModel):
    waba_id: str
    phone_number_id: str
    access_token: str
    webhook_verify_token: str

class WhatsAppConnectionOut(BaseModel):
    id: uuid.UUID
    waba_id: str
    phone_number_id: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
