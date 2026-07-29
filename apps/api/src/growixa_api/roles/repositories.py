from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.roles.models import Role


async def get_role_by_name(session: AsyncSession, name: str) -> Role | None:
    result = await session.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def list_roles(session: AsyncSession) -> Sequence[Role]:
    result = await session.execute(select(Role).order_by(Role.name))
    return result.scalars().all()
