import uuid
import random
from typing import Annotated
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.permissions.dependencies import RequirePermission, get_current_account_id
from growixa_api.analytics_engine.models import MetricSnapshot
from growixa_api.analytics_engine.schemas import AnalyticsDashboardOut, TimeSeriesPoint, GrowthInsightsOut
from growixa_api.ai.services import generate

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics Engine"],
    dependencies=[Depends(RequirePermission("analytics:read"))],
)


@router.get("/dashboard", response_model=AnalyticsDashboardOut)
async def get_dashboard_metrics(
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsDashboardOut:
    """
    Fetch pre-aggregated metrics snapshots for the dashboard.
    If none exist for this account, seeds 30 days of mock data.
    """
    # Fetch recent snapshots (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    
    result = await session.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.account_id == account_id)
        .where(MetricSnapshot.date >= thirty_days_ago)
        .order_by(MetricSnapshot.date.asc())
    )
    snapshots = result.scalars().all()
    
    if not snapshots:
        # Seed 30 days of mock data
        base_followers = 15000
        for i in range(30):
            d = (datetime.now(timezone.utc) - timedelta(days=(29-i))).date()
            base_followers += random.randint(-50, 300)
            engagement = random.randint(1000, 5000)
            reach = engagement * random.randint(3, 8)
            
            snap = MetricSnapshot(
                account_id=account_id,
                entity_type="CHANNEL",
                entity_id="mock_channel_1",
                date=d,
                metrics_jsonb={
                    "followers": base_followers,
                    "engagement": engagement,
                    "reach": reach
                }
            )
            session.add(snap)
            snapshots.append(snap)
        
        await session.commit()
        # No need to refresh, we just use the list we built
        
    # Aggregate for the response
    chart_data = []
    # Group by date
    by_date: dict[str, dict[str, int]] = {}
    
    for s in snapshots:
        d_str = s.date.strftime("%b %d")
        if d_str not in by_date:
            by_date[d_str] = {"followers": 0, "engagement": 0, "reach": 0}
        
        metrics = s.metrics_jsonb
        by_date[d_str]["followers"] += metrics.get("followers", 0)
        by_date[d_str]["engagement"] += metrics.get("engagement", 0)
        by_date[d_str]["reach"] += metrics.get("reach", 0)
        
    for d_str, totals in by_date.items():
        chart_data.append(
            TimeSeriesPoint(
                name=d_str,
                followers=totals["followers"],
                engagement=totals["engagement"],
                reach=totals["reach"]
            )
        )
        
    # Calculate simple totals and mock changes
    total_followers = chart_data[-1].followers if chart_data else 0
    total_eng = sum(c.engagement for c in chart_data)
    total_reach = sum(c.reach for c in chart_data)
    
    return AnalyticsDashboardOut(
        total_followers=total_followers,
        followers_change=12.5,
        total_engagement=total_eng,
        engagement_change=5.4,
        total_reach=total_reach,
        reach_change=-2.1,
        chart_data=chart_data
    )

@router.get("/insights", response_model=GrowthInsightsOut)
async def get_growth_insights(
    account_id: Annotated[uuid.UUID, Depends(get_current_account_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GrowthInsightsOut:
    """
    Generate AI-driven growth insights from the last 30 days of metrics.
    """
    # Fetch recent snapshots
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    result = await session.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.account_id == account_id)
        .where(MetricSnapshot.date >= thirty_days_ago)
        .order_by(MetricSnapshot.date.asc())
    )
    snapshots = result.scalars().all()
    
    if not snapshots:
        return GrowthInsightsOut(
            insights=["Not enough data to generate insights."],
            recommendations=[],
            topics=[]
        )
    
    # Serialize data for the prompt
    brief_data = []
    for s in snapshots:
        brief_data.append({
            "date": s.date.isoformat(),
            "metrics": s.metrics_jsonb
        })
    
    # Call the AI capability
    # In a real scenario, we might want to pass the actor_id, but here it's an automated background/dashboard fetch.
    # For now, we will pass account_id as actor_id just to satisfy the generate signature, 
    # since this is a read endpoint without a specific user action trigger (or we could extract current_user).
    # Since router doesn't have actor_id by default, we'll just use account_id for the log.
    generation = await generate(
        session,
        account_id=account_id,
        actor_id=account_id, # Using account_id as actor_id for automated insights
        capability="GROWTH_INSIGHTS",
        brief=str(brief_data),
        existing_text=None,
        instruction=None,
        linked_entity_type=None,
        linked_entity_id=None
    )
    
    output = generation.output or {}
    return GrowthInsightsOut(
        insights=output.get("insights", ["Trend analysis complete."]),
        recommendations=output.get("recommendations", ["Keep posting consistently."]),
        topics=output.get("topics", ["Industry News", "Behind the Scenes"])
    )
