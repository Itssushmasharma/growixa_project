import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.users.models import User, UserInvitation


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    # User.email is CITEXT (case-insensitive) at the DB level — no normalization needed here.
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession, *, email: str, password_hash: str, full_name: str
) -> User:
    user = User(email=email, password_hash=password_hash, full_name=full_name)
    session.add(user)
    await session.flush()
    return user


async def create_invitation(
    session: AsyncSession,
    *,
    email: str,
    token_hash: str,
    role_id: uuid.UUID,
    invited_by_user_id: uuid.UUID,
    expires_at: datetime,
) -> UserInvitation:
    invitation = UserInvitation(
        email=email,
        token_hash=token_hash,
        role_id=role_id,
        invited_by_user_id=invited_by_user_id,
        expires_at=expires_at,
    )
    session.add(invitation)
    await session.flush()
    return invitation


async def get_invitation_by_token_hash(
    session: AsyncSession, token_hash: str
) -> UserInvitation | None:
    result = await session.execute(
        select(UserInvitation).where(UserInvitation.token_hash == token_hash)
    )
    return result.scalar_one_or_none()
