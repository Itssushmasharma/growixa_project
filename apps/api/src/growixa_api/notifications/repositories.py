from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.notifications.models import PlatformEmailProviderConfig


async def get_active_platform_config(session: AsyncSession) -> PlatformEmailProviderConfig | None:
    result = await session.execute(
        select(PlatformEmailProviderConfig).where(PlatformEmailProviderConfig.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def deactivate_active_platform_config(session: AsyncSession) -> None:
    await session.execute(
        update(PlatformEmailProviderConfig)
        .where(PlatformEmailProviderConfig.is_active.is_(True))
        .values(is_active=False)
    )


async def create_platform_config(
    session: AsyncSession, fields: dict[str, Any]
) -> PlatformEmailProviderConfig:
    config = PlatformEmailProviderConfig(**fields)
    session.add(config)
    await session.flush()
    return config
