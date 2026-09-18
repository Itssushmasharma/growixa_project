from pydantic import BaseModel
from typing import List

class TimeSeriesPoint(BaseModel):
    name: str
    followers: int
    engagement: int
    reach: int

class AnalyticsDashboardOut(BaseModel):
    total_followers: int
    followers_change: float
    total_engagement: int
    engagement_change: float
    total_reach: int
    reach_change: float
    chart_data: List[TimeSeriesPoint]

class GrowthInsightsOut(BaseModel):
    insights: List[str]
    recommendations: List[str]
    topics: List[str]
