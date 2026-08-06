import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.company.models import CompanyProfile
from growixa_api.company.repositories import get_company_profile, upsert_company_profile
from growixa_api.company.schemas import CompanyProfileIn


async def get_profile(session: AsyncSession, account_id: uuid.UUID) -> CompanyProfile | None:
    return await get_company_profile(session, account_id)


async def save_profile(
    session: AsyncSession, account_id: uuid.UUID, data: CompanyProfileIn
) -> CompanyProfile:
    """Get-then-upsert the per-account singleton company_profile row.

    Not race-safe against two concurrent first-time saves (a unique constraint or advisory
    lock would close that gap) — acceptable for Sprint 1, where company settings are edited
    by a single admin at a time, not a concern under concurrent multi-admin writes.
    """
    existing = await get_company_profile(session, account_id)
    return await upsert_company_profile(session, existing, account_id, data.model_dump())
