"""Ads Hub API router for Google Ads & Meta Ads campaign workspace."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/ads",
    tags=["ads-hub"],
)


class AdCampaignIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    platform: str = Field(description="google_ads or meta_ads")
    objective: str = Field(description="LEAD_GEN, CONVERSIONS, TRAFFIC, BRAND_AWARENESS")
    daily_budget_usd: float = Field(gt=0)
    target_audience: str = Field(min_length=3)
    destination_url: str = Field(min_length=5)


class AdCampaignOut(AdCampaignIn):
    id: str
    status: str
    utm_url: str
    clicks: int = 0
    conversions: int = 0
    spend_usd: float = 0.0
    roas: float = 0.0


class UtmBuildIn(BaseModel):
    destination_url: str
    source: str = Field(default="google")
    medium: str = Field(default="cpc")
    campaign_name: str
    term: str | None = None
    content: str | None = None


_CAMPAIGNS_STORE: list[dict[str, Any]] = [
    {
        "id": "ad_camp_01",
        "name": "Q4 Outbound SaaS Lead Gen",
        "platform": "google_ads",
        "objective": "LEAD_GEN",
        "daily_budget_usd": 150.0,
        "target_audience": "Founders & VP Marketing in US/IN",
        "destination_url": "https://growixa.com/pricing",
        "status": "ACTIVE",
        "utm_url": "https://growixa.com/pricing?utm_source=google&utm_medium=cpc&utm_campaign=q4_outbound",
        "clicks": 1420,
        "conversions": 184,
        "spend_usd": 680.0,
        "roas": 3.42,
    },
    {
        "id": "ad_camp_02",
        "name": "Instagram Retargeting Reel",
        "platform": "meta_ads",
        "objective": "CONVERSIONS",
        "daily_budget_usd": 75.0,
        "target_audience": "Website Visitors 30D",
        "destination_url": "https://growixa.com/register",
        "status": "ACTIVE",
        "utm_url": "https://growixa.com/register?utm_source=meta&utm_medium=paid_social&utm_campaign=retargeting_reel",
        "clicks": 980,
        "conversions": 112,
        "spend_usd": 320.0,
        "roas": 4.15,
    },
]


@router.get("/campaigns", response_model=list[AdCampaignOut])
async def list_campaigns() -> list[AdCampaignOut]:
    return [AdCampaignOut(**c) for c in _CAMPAIGNS_STORE]


@router.post("/campaigns", response_model=AdCampaignOut)
async def create_campaign(payload: AdCampaignIn) -> AdCampaignOut:
    utm_url = f"{payload.destination_url}?utm_source={payload.platform}&utm_medium=paid&utm_campaign={payload.name.lower().replace(' ', '_')}"
    new_camp = {
        "id": f"ad_camp_0{len(_CAMPAIGNS_STORE) + 1}",
        **payload.model_dump(),
        "status": "ACTIVE",
        "utm_url": utm_url,
        "clicks": 0,
        "conversions": 0,
        "spend_usd": 0.0,
        "roas": 0.0,
    }
    _CAMPAIGNS_STORE.append(new_camp)
    return AdCampaignOut(**new_camp)


@router.post("/utm-builder")
async def build_utm(payload: UtmBuildIn) -> dict[str, str]:
    base = payload.destination_url.split("?")[0]
    utm = f"{base}?utm_source={payload.source}&utm_medium={payload.medium}&utm_campaign={payload.campaign_name}"
    if payload.term:
        utm += f"&utm_term={payload.term}"
    if payload.content:
        utm += f"&utm_content={payload.content}"
    return {"utm_url": utm}
