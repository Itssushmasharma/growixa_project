import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.platform_auth.models import (
    PlatformAdmin,
    PlatformPermission,
    PlatformRolePermission,
)


async def get_platform_admin_by_email(session: AsyncSession, email: str) -> PlatformAdmin | None:
    result = await session.execute(select(PlatformAdmin).where(PlatformAdmin.email == email))
    return result.scalar_one_or_none()


async def platform_admin_has_permission(
    session: AsyncSession, platform_admin_id: uuid.UUID, code: str
) -> bool:
    stmt = (
        select(PlatformPermission.id)
        .join(PlatformRolePermission, PlatformRolePermission.permission_id == PlatformPermission.id)
        .join(PlatformAdmin, PlatformAdmin.role == PlatformRolePermission.role)
        .where(PlatformAdmin.id == platform_admin_id, PlatformPermission.code == code)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.first() is not None


async def list_permission_codes_for_platform_admin(
    session: AsyncSession, platform_admin_id: uuid.UUID
) -> set[str]:
    stmt = (
        select(PlatformPermission.code)
        .join(PlatformRolePermission, PlatformRolePermission.permission_id == PlatformPermission.id)
        .join(PlatformAdmin, PlatformAdmin.role == PlatformRolePermission.role)
        .where(PlatformAdmin.id == platform_admin_id)
    )
    result = await session.execute(stmt)
    return set(result.scalars().all())
