"""Business Presence & Landing Page Builder API router."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/business-presence",
    tags=["business-presence"],
)


class SiteIn(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=100)
    hero_headline: str = Field(min_length=3)
    hero_subhead: str = Field(min_length=3)
    cta_button_text: str = Field(default="Get Started Free")


class SiteOut(SiteIn):
    id: str
    published_url: str
    views_count: int = 0
    conversions_count: int = 0


class CtaLinkIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    destination_url: str = Field(min_length=5)
    category: str = Field(default="Social Bio Link")


class CtaLinkOut(CtaLinkIn):
    id: str
    short_slug: str
    clicks: int = 0


_SITES_STORE: list[dict[str, Any]] = [
    {
        "id": "site_01",
        "title": "Growixa Product Launch Landing Page",
        "slug": "grow-v2",
        "hero_headline": "Accelerate GTM Execution with AI",
        "hero_subhead": "The unified growth workspace connecting CRM, Email relays, and Social automation.",
        "cta_button_text": "Start Free Workspace →",
        "published_url": "https://growixa.com/p/grow-v2",
        "views_count": 3420,
        "conversions_count": 412,
    }
]

_LINKS_STORE: list[dict[str, Any]] = [
    {
        "id": "link_01",
        "title": "Book 1-on-1 Growth Demo",
        "destination_url": "https://growixa.com/contact",
        "category": "Social Bio Link",
        "short_slug": "demo",
        "clicks": 890,
    },
    {
        "id": "link_02",
        "title": "View Pricing & Upgrade Plans",
        "destination_url": "https://growixa.com/pricing",
        "category": "Email Footer Link",
        "short_slug": "pricing-link",
        "clicks": 1240,
    },
]


@router.get("/sites", response_model=list[SiteOut])
async def list_sites() -> list[SiteOut]:
    return [SiteOut(**s) for s in _SITES_STORE]


@router.post("/sites", response_model=SiteOut)
async def create_site(payload: SiteIn) -> SiteOut:
    site_id = f"site_custom_{len(_SITES_STORE) + 1}"
    new_site = {
        "id": site_id,
        **payload.model_dump(),
        "published_url": f"https://growixa.com/p/{payload.slug}",
        "views_count": 0,
        "conversions_count": 0,
    }
    _SITES_STORE.append(new_site)
    return SiteOut(**new_site)


@router.get("/links", response_model=list[CtaLinkOut])
async def list_links() -> list[CtaLinkOut]:
    return [CtaLinkOut(**l) for l in _LINKS_STORE]


@router.post("/links", response_model=CtaLinkOut)
async def create_link(payload: CtaLinkIn) -> CtaLinkOut:
    link_id = f"link_custom_{len(_LINKS_STORE) + 1}"
    short_slug = payload.title.lower().replace(" ", "-")[:16]
    new_link = {
        "id": link_id,
        **payload.model_dump(),
        "short_slug": short_slug,
        "clicks": 0,
    }
    _LINKS_STORE.append(new_link)
    return CtaLinkOut(**new_link)
