from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.seo.analyzer import seo_analyzer

router = APIRouter(prefix="/seo", tags=["seo"])


class SEOAnalyzeIn(BaseModel):
    url: str


class SEOAnalyzeOut(BaseModel):
    url: str
    score: int
    title: str | None = None
    description: str | None = None
    h1_count: int = 0
    image_count: int = 0
    images_missing_alt: int = 0
    is_https: bool = False
    warnings: List[str]
    recommendations: List[str]
    error: str | None = None


@router.post("/analyze", response_model=SEOAnalyzeOut)
async def analyze_url(
    payload: SEOAnalyzeIn,
    # In a real app we might require auth or account_id here
    # account_id: uuid.UUID = Depends(get_current_account_id),
) -> SEOAnalyzeOut:
    """Analyze a given URL for SEO health."""
    try:
        result = await seo_analyzer.analyze(payload.url)
        return SEOAnalyzeOut(**result)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"SEO Analysis failed: {str(e)}")
