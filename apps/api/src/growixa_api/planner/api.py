"""AI Marketing & GTM Campaign Planner API router."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/planner",
    tags=["planner"],
)


class MarketingPlanIn(BaseModel):
    product_name: str = Field(min_length=1, max_length=100)
    target_audience: str = Field(min_length=3)
    primary_goal: str = Field(description="LEAD_GEN, BRAND_AWARENESS, SALES_CONVERSION, APP_INSTALLS")
    monthly_budget_usd: float = Field(gt=0)


class MarketingPlanOut(BaseModel):
    plan_id: str
    product_name: str
    recommended_channels: list[dict[str, str]]
    content_milestones: list[dict[str, str]]
    suggested_budget_allocation: dict[str, str]


_TASKS_STORE: list[dict[str, Any]] = [
    {
        "id": "task_01",
        "title": "Design Instagram Launch Carousel",
        "channel": "Instagram",
        "status": "IN_PROGRESS",
        "due_date": "2026-09-25",
        "owner": "Creative Studio",
    },
    {
        "id": "task_02",
        "title": "Setup Postmark Transactional Email Relay",
        "channel": "Email",
        "status": "COMPLETED",
        "due_date": "2026-09-22",
        "owner": "DevOps / Tech",
    },
    {
        "id": "task_03",
        "title": "Launch Google Ads High Intent Keyword Campaign",
        "channel": "Google Ads",
        "status": "TODO",
        "due_date": "2026-09-28",
        "owner": "Growth Team",
    },
]


@router.get("/tasks")
async def list_tasks() -> list[dict[str, Any]]:
    return _TASKS_STORE


@router.post("/generate-plan", response_model=MarketingPlanOut)
async def generate_plan(payload: MarketingPlanIn) -> MarketingPlanOut:
    plan_id = f"plan_{payload.product_name.lower().replace(' ', '_')}_2026"
    return MarketingPlanOut(
        plan_id=plan_id,
        product_name=payload.product_name,
        recommended_channels=[
            {"channel": "Meta Ads & Instagram", "focus": "Visual social stories & targeted lead forms", "weight": "40%"},
            {"channel": "Google Search Ads", "focus": "Capture active high-intent keyword searches", "weight": "35%"},
            {"channel": "Email Drip & Postmark Relays", "focus": "Automated welcome sequence & trial nurture", "weight": "25%"},
        ],
        content_milestones=[
            {"week": "Week 1", "action": "Setup brand kit, tracking pixels, and launch landing page."},
            {"week": "Week 2", "action": "Run A/B creative testing on Instagram and Google Search ads."},
            {"week": "Week 3", "action": "Trigger automated WhatsApp & Email follow-ups to captured leads."},
            {"week": "Week 4", "action": "Review conversion telemetry and scale winning ad channels."},
        ],
        suggested_budget_allocation={
            "Paid Ads (Google/Meta)": f"${payload.monthly_budget_usd * 0.6:.2f}",
            "Creative & Content Assets": f"${payload.monthly_budget_usd * 0.25:.2f}",
            "Email & SMS Relays": f"${payload.monthly_budget_usd * 0.15:.2f}",
        },
    )
