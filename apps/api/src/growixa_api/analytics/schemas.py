import uuid

from pydantic import BaseModel


class CampaignReportOut(BaseModel):
    campaign_id: uuid.UUID
    sent: int
    delivered: int
    opened: int
    clicked: int
    total_opened: int = 0
    total_clicked: int = 0
    open_rate_pct: float | None = None
    click_rate_pct: float | None = None
    click_to_open_rate_pct: float | None = None
    bounced: int
    complained: int
