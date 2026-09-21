"""Creative Studio API router for AI social creatives, banners, flyers, ad stories, and brand kit."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from growixa_api.permissions.dependencies import RequirePermission

router = APIRouter(
    prefix="/creative",
    tags=["creative-studio"],
)


class BrandKitIn(BaseModel):
    brand_name: str = Field(min_length=1, max_length=100)
    primary_color: str = Field(default="#6D0626")
    secondary_color: str = Field(default="#F7F1EA")
    accent_color: str = Field(default="#A01B42")
    font_family: str = Field(default="Inter, sans-serif")
    logo_url: str | None = None
    tagline: str | None = None


class BrandKitOut(BrandKitIn):
    account_id: str = "demo-account"


class CreativeGenerateIn(BaseModel):
    preset_type: str = Field(
        description="instagram_post, story_reel, facebook_ad, linkedin_banner, flyer_poster, business_card"
    )
    prompt: str = Field(min_length=3, max_length=1000)
    headline: str | None = None
    cta_text: str | None = None


class CreativeGenerateOut(BaseModel):
    id: str
    preset_type: str
    headline: str
    cta_text: str
    image_url: str
    width: int
    height: int
    suggested_captions: list[str]


PRESETS = [
  {"id": "instagram_post", "name": "Instagram Post", "width": 1080, "height": 1080, "aspect": "1:1"},
  {"id": "story_reel", "name": "Instagram Story / Reel", "width": 1080, "height": 1920, "aspect": "9:16"},
  {"id": "facebook_ad", "name": "Facebook Feed Ad", "width": 1200, "height": 628, "aspect": "1.91:1"},
  {"id": "linkedin_banner", "name": "LinkedIn Banner", "width": 1584, "height": 396, "aspect": "4:1"},
  {"id": "flyer_poster", "name": "Marketing Flyer / Poster", "width": 1200, "height": 1600, "aspect": "3:4"},
  {"id": "business_card", "name": "Digital Business Card", "width": 1050, "height": 600, "aspect": "1.75:1"},
]

# Simple in-memory brand kit fallback
_BRAND_KIT_STORE: dict[str, Any] = {
    "brand_name": "Growixa Partner",
    "primary_color": "#6D0626",
    "secondary_color": "#F7F1EA",
    "accent_color": "#A01B42",
    "font_family": "Inter, sans-serif",
    "logo_url": "/assets/brand/growixa_logo.png",
    "tagline": "Accelerate Digital Growth",
}


@router.get("/presets")
async def list_presets() -> list[dict[str, Any]]:
    return PRESETS


@router.get("/brand-kit", response_model=BrandKitOut)
async def get_brand_kit() -> BrandKitOut:
    return BrandKitOut(**_BRAND_KIT_STORE)


@router.post("/brand-kit", response_model=BrandKitOut)
async def save_brand_kit(payload: BrandKitIn) -> BrandKitOut:
    _BRAND_KIT_STORE.update(payload.model_dump())
    return BrandKitOut(**_BRAND_KIT_STORE)


@router.post("/generate", response_model=CreativeGenerateOut)
async def generate_creative(payload: CreativeGenerateIn) -> CreativeGenerateOut:
    preset = next((p for p in PRESETS if p["id"] == payload.preset_type), PRESETS[0])
    headline = payload.headline or f"Elevate Your Brand with {payload.prompt[:30]}"
    cta = payload.cta_text or "Learn More →"
    
    return CreativeGenerateOut(
        id=f"cr_{payload.preset_type}_101",
        preset_type=payload.preset_type,
        headline=headline,
        cta_text=cta,
        image_url="/assets/3d/growixa_3d_fluid_core.jpg",
        width=preset["width"],
        height=preset["height"],
        suggested_captions=[
            f"🔥 {headline} — Transform your GTM campaign with Growixa AI studio. Click link in bio!",
            f"✨ Ready to scale? {headline} Learn how our automated workflow delivers results.",
            f"🚀 {headline}. Built for modern growth teams. #growwithgrowixa #digitalmarketing"
        ]
    )
