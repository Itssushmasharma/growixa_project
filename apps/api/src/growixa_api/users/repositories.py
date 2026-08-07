import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.roles.models import Role
from growixa_api.users.models import User, UserInvitation, UserRole


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    # Deliberately NOT account_id-scoped: this is the login lookup, called before any
    # account is known. email is globally unique (GRX-SAAS-001 Phase A note on User.account_id)
    # precisely so this stays a single unambiguous lookup. User.email is CITEXT
    # (case-insensitive) at the DB level — no normalization needed here.
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession, user_id: uuid.UUID, *, account_id: uuid.UUID
) -> User | None:
    # account_id-scoped so a caller can never fetch (and then act on) a user from another
    # account by guessing/enumerating a UUID -- returns None indistinguishably from "does
    # not exist at all", same as every other account-scoped lookup in this codebase.
    result = await session.execute(
        select(User).where(User.id == user_id, User.account_id == account_id)
    )
    return result.scalar_one_or_none()


async def list_users(session: AsyncSession, *, account_id: uuid.UUID) -> Sequence[User]:
    result = await session.execute(
        select(User).where(User.account_id == account_id).order_by(User.created_at)
    )
    return result.scalars().all()


async def list_role_names_by_user_id(
    session: AsyncSession, *, account_id: uuid.UUID
) -> dict[uuid.UUID, list[str]]:
    stmt = (
        select(UserRole.user_id, Role.name)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.account_id == account_id)
    )
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
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    assigned_by_user_id: uuid.UUID,
) -> None:
    await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
    session.add(
        UserRole(
            account_id=account_id,
            user_id=user_id,
            role_id=role_id,
            assigned_by_user_id=assigned_by_user_id,
        )
    )
    await session.flush()


async def create_user(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    email: str,
    password_hash: str,
    full_name: str,
    status: str = "ACTIVE",
) -> User:
    user = User(
        account_id=account_id,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        status=status,
    )
    session.add(user)
    await session.flush()
    return user


async def create_invitation(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    email: str,
    token_hash: str,
    role_id: uuid.UUID,
    invited_by_user_id: uuid.UUID,
    expires_at: datetime,
) -> UserInvitation:
    invitation = UserInvitation(
        account_id=account_id,
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
    # Not account-scoped: the accepting caller is unauthenticated (no account context yet)
    # -- the invitation row itself carries the account_id the new user will join.
    result = await session.execute(
        select(UserInvitation).where(UserInvitation.token_hash == token_hash)
    )
    return result.scalar_one_or_none()
