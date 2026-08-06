import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.brand.schemas import BrandProfileIn, BrandProfileOut
from growixa_api.brand.services import CompanyProfileRequiredError, get_profile, save_profile
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/brand", tags=["brand"])

_require_view = require_permission("company.settings.view")
_require_edit = require_permission("company.settings.edit")


@router.get("/profile", response_model=BrandProfileOut | None)
async def read_brand_profile(
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> BrandProfileOut | None:
    profile = await get_profile(session, account_id)
    return BrandProfileOut.model_validate(profile) if profile is not None else None


@router.put("/profile", response_model=BrandProfileOut)
async def update_brand_profile(
    payload: BrandProfileIn,
    _actor_id: uuid.UUID = Depends(_require_edit),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> BrandProfileOut:
    try:
        profile = await save_profile(session, account_id, payload)
    except CompanyProfileRequiredError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Company profile must be created before brand settings",
        ) from exc
    await session.commit()
    return BrandProfileOut.model_validate(profile)
