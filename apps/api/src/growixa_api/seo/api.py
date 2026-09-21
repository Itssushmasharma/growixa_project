"""SEO Audit & Optimization API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from growixa_api.permissions.dependencies import RequirePermission
from growixa_api.seo.analyzer import seo_analyzer

router = APIRouter(
    prefix="/seo",
    tags=["seo"],
)


class SEOAnalyzeIn(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class SEOAnalyzeOut(BaseModel):
    url: str
    score: int
    title: str | None = None
    description: str | None = None
    h1_count: int = 0
    image_count: int = 0
    images_missing_alt: int = 0
    is_https: bool = False
    warnings: list[str]
    recommendations: list[str]
    error: str | None = None


class KeywordExploreIn(BaseModel):
    seed_keyword: str = Field(min_length=2, max_length=100)


class KeywordItem(BaseModel):
    keyword: str
    search_volume: int
    difficulty: str
    cpc_usd: float
    intent: str


@router.post("/analyze", response_model=SEOAnalyzeOut)
async def analyze_url(payload: SEOAnalyzeIn) -> SEOAnalyzeOut:
    """Analyze real-time SEO structure of the target website URL."""
    result = await seo_analyzer.analyze(payload.url)
    return SEOAnalyzeOut(**result)


@router.post("/keywords/research", response_model=list[KeywordItem])
async def research_keywords(payload: KeywordExploreIn) -> list[KeywordItem]:
    seed = payload.seed_keyword.lower()
    return [
        KeywordItem(
            keyword=f"best {seed} software",
            search_volume=14200,
            difficulty="MEDIUM",
            cpc_usd=3.45,
            intent="COMMERCIAL",
        ),
        KeywordItem(
            keyword=f"how to automate {seed}",
            search_volume=8900,
            difficulty="EASY",
            cpc_usd=1.80,
            intent="INFORMATIONAL",
        ),
        KeywordItem(
            keyword=f"{seed} integration platform",
            search_volume=6400,
            difficulty="HIGH",
            cpc_usd=5.20,
            intent="TRANSACTIONAL",
        ),
        KeywordItem(
            keyword=f"free {seed} templates",
            search_volume=18500,
            difficulty="EASY",
            cpc_usd=0.95,
            intent="INFORMATIONAL",
        ),
    ]
