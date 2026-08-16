import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.company.schemas import CompanyProfileIn, CompanyProfileOut
from growixa_api.company.services import get_profile, save_profile
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/company", tags=["company"])

_require_view = require_permission("company.settings.view")
_require_edit = require_permission("company.settings.edit")


@router.get("/profile", response_model=CompanyProfileOut | None)
async def read_company_profile(
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> CompanyProfileOut | None:
    profile = await get_profile(session, account_id)
    return CompanyProfileOut.model_validate(profile) if profile is not None else None


@router.put("/profile", response_model=CompanyProfileOut)
async def update_company_profile(
    payload: CompanyProfileIn,
    _actor_id: uuid.UUID = Depends(_require_edit),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> CompanyProfileOut:
    profile = await save_profile(session, account_id, payload)
    await session.commit()
    await session.refresh(profile)
    return CompanyProfileOut.model_validate(profile)
