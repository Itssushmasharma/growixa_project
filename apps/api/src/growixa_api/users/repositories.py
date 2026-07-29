import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.roles.models import Role
from growixa_api.users.models import User, UserInvitation, UserRole


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    # User.email is CITEXT (case-insensitive) at the DB level — no normalization needed here.
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def list_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


async def list_role_names_by_user_id(session: AsyncSession) -> dict[uuid.UUID, list[str]]:
    stmt = select(UserRole.user_id, Role.name).join(Role, Role.id == UserRole.role_id)
    result = await session.execute(stmt)
    mapping: dict[uuid.UUID, list[str]] = {}
    for user_id, role_name in result.all():
        mapping.setdefault(user_id, []).append(role_name)
    return mapping


async def list_role_names_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[str]:
    stmt = (
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def replace_user_role(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    assigned_by_user_id: uuid.UUID,
) -> None:
    await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
    session.add(UserRole(user_id=user_id, role_id=role_id, assigned_by_user_id=assigned_by_user_id))
    await session.flush()


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
