import uuid

from pydantic import BaseModel


class CampaignReportOut(BaseModel):
    campaign_id: uuid.UUID
    sent: int
    delivered: int
    opened: int
    clicked: int
    bounced: int
    complained: int
