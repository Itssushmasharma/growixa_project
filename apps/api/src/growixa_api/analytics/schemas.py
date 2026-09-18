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
    bounce_rate_pct: float | None = None
    unsubscribe_count: int = 0


class CampaignTimeseriesPoint(BaseModel):
    bucket: str
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    bounced: int = 0


class CampaignTimeseriesOut(BaseModel):
    campaign_id: uuid.UUID
    points: list[CampaignTimeseriesPoint]


class CampaignComparisonOut(BaseModel):
    campaign_id: uuid.UUID
    recipient_type: str
    recipient_count: int
    campaign_open_rate_pct: float | None = None
    campaign_click_rate_pct: float | None = None
    campaign_bounce_rate_pct: float | None = None
    account_avg_open_rate_pct: float | None = None
    account_avg_click_rate_pct: float | None = None
    account_avg_bounce_rate_pct: float | None = None
