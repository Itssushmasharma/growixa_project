from pydantic import BaseModel


class TestSendIn(BaseModel):
    to_email: str


class CampaignSendOut(BaseModel):
    job_id: str
