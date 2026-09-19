"""SEO audit availability while the isolated crawler is pending."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/seo", tags=["seo"])


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


@router.post("/analyze", response_model=SEOAnalyzeOut)
async def analyze_url(payload: SEOAnalyzeIn) -> SEOAnalyzeOut:
    """Never fetch arbitrary URLs from the API's trusted network."""
    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "FEATURE_PENDING",
            "message": "Website audits are pending secure crawler integration.",
        },
    )
