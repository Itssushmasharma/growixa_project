import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.users.models import User


async def get_account_id_for_user(session: AsyncSession, user_id: uuid.UUID) -> uuid.UUID | None:
    result = await session.execute(select(User.account_id).where(User.id == user_id))
    return result.scalar_one_or_none()
