from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.users.models import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    # User.email is CITEXT (case-insensitive) at the DB level — no normalization needed here.
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
