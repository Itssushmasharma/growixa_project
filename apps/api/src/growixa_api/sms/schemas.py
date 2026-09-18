import uuid
from pydantic import BaseModel, ConfigDict

class SMSConnectionIn(BaseModel):
    provider: str
    account_sid: str
    auth_token: str
    sender_number: str

class SMSConnectionOut(BaseModel):
    id: uuid.UUID
    provider: str
    account_sid: str
    sender_number: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
