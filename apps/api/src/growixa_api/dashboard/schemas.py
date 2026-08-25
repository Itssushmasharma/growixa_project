import uuid

from pydantic import BaseModel


class QuotaStatusOut(BaseModel):
    plan_name: str
    contact_usage: int
    contact_limit: int | None
    email_usage: int
    email_limit: int | None
    ai_usage: int
    ai_limit: int | None
    ai_credits_remaining: int


class CampaignStatusBreakdownOut(BaseModel):
    draft: int
    scheduled: int
    sending: int
    sent: int
    cancelled: int
    failed: int


class ContactGrowthPointOut(BaseModel):
    month: str
    contacts: int


class RecentCampaignOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    sent_count: int
    open_rate_pct: float | None


class ActivityStreamItemOut(BaseModel):
    id: uuid.UUID
    event_type: str  # OPENED or CLICKED
    contact_email: str
    campaign_id: uuid.UUID
    campaign_name: str
    occurred_at: str


class DashboardOverviewOut(BaseModel):
    total_contacts: int
    active_campaigns: int
    scheduled_social_posts: int
    email_open_rate_pct: float | None
    email_click_rate_pct: float | None
    email_ctor_pct: float | None = None
    quota: QuotaStatusOut
    campaign_status_breakdown: CampaignStatusBreakdownOut
    contact_growth_6_months: list[ContactGrowthPointOut]
    recent_campaigns: list[RecentCampaignOut]
    recent_activity: list[ActivityStreamItemOut] = []
