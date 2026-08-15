from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.email_validation.models import PlatformEmailValidationProviderConfig


async def get_active_platform_config(
    session: AsyncSession,
) -> PlatformEmailValidationProviderConfig | None:
    result = await session.execute(
        select(PlatformEmailValidationProviderConfig).where(
            PlatformEmailValidationProviderConfig.is_active.is_(True)
        )
    )
    return result.scalar_one_or_none()


async def deactivate_active_platform_config(session: AsyncSession) -> None:
    await session.execute(
        update(PlatformEmailValidationProviderConfig)
        .where(PlatformEmailValidationProviderConfig.is_active.is_(True))
        .values(is_active=False)
    )


async def create_platform_config(
    session: AsyncSession, fields: dict[str, Any]
) -> PlatformEmailValidationProviderConfig:
    config = PlatformEmailValidationProviderConfig(**fields)
    session.add(config)
    await session.flush()
    return config
