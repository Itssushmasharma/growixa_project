import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.brand.models import BrandProfile
from growixa_api.brand.repositories import get_brand_profile, upsert_brand_profile
from growixa_api.brand.schemas import BrandProfileIn
from growixa_api.company.repositories import get_company_profile


class CompanyProfileRequiredError(Exception):
    """Raised when brand settings are read/written before a company profile exists.

    brand_profiles.company_id is a NOT NULL FK to company_profile.id, so there is nothing
    to attach a brand profile to yet — per MODULE_BOUNDARIES.md, `brand` depends on
    `company`, and this is that dependency showing up as an ordering requirement.
    """


async def get_profile(session: AsyncSession, account_id: uuid.UUID) -> BrandProfile | None:
    company = await get_company_profile(session, account_id)
    if company is None:
        return None
    return await get_brand_profile(session, account_id)


async def save_profile(
    session: AsyncSession, account_id: uuid.UUID, data: BrandProfileIn
) -> BrandProfile:
    company = await get_company_profile(session, account_id)
    if company is None:
        raise CompanyProfileRequiredError
    existing = await get_brand_profile(session, account_id)
    return await upsert_brand_profile(session, existing, account_id, company.id, data.model_dump())
