from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.company.models import CompanyProfile


async def get_company_profile(session: AsyncSession) -> CompanyProfile | None:
    result = await session.execute(select(CompanyProfile).limit(1))
    return result.scalar_one_or_none()


async def upsert_company_profile(
    session: AsyncSession,
    existing: CompanyProfile | None,
    fields: dict[str, Any],
) -> CompanyProfile:
    if existing is None:
        profile = CompanyProfile(**fields)
        session.add(profile)
    else:
        for key, value in fields.items():
            setattr(existing, key, value)
        profile = existing
    await session.flush()
    return profile
