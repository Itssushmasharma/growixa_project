from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.company.models import CompanyProfile
from growixa_api.company.repositories import get_company_profile, upsert_company_profile
from growixa_api.company.schemas import CompanyProfileIn


async def get_profile(session: AsyncSession) -> CompanyProfile | None:
    return await get_company_profile(session)


async def save_profile(session: AsyncSession, data: CompanyProfileIn) -> CompanyProfile:
    """Get-then-upsert the singleton company_profile row.

    Not race-safe against two concurrent first-time saves (a unique constraint or advisory
    lock would close that gap) — acceptable for Sprint 1, where company settings are edited
    by a single admin at a time, not a concern under concurrent multi-admin writes.
    """
    existing = await get_company_profile(session)
    return await upsert_company_profile(session, existing, data.model_dump())
