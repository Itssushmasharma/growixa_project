import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.brand.models import BrandProfile


async def get_brand_profile(session: AsyncSession, company_id: uuid.UUID) -> BrandProfile | None:
    result = await session.execute(
        select(BrandProfile).where(BrandProfile.company_id == company_id).limit(1)
    )
    return result.scalar_one_or_none()


async def upsert_brand_profile(
    session: AsyncSession,
    existing: BrandProfile | None,
    company_id: uuid.UUID,
    fields: dict[str, Any],
) -> BrandProfile:
    if existing is None:
        profile = BrandProfile(company_id=company_id, **fields)
        session.add(profile)
    else:
        for key, value in fields.items():
            setattr(existing, key, value)
        profile = existing
    await session.flush()
    return profile
