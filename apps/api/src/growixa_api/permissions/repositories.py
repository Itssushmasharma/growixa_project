import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.permissions.models import Permission, RolePermission
from growixa_api.users.models import User, UserRole


async def user_has_permission(session: AsyncSession, user_id: uuid.UUID, code: str) -> bool:
    stmt = (
        select(Permission.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(User, User.id == UserRole.user_id)
        .join(Account, Account.id == User.account_id)
        .where(
            User.status == "ACTIVE",
            Account.status == "ACTIVE",
            UserRole.account_id == User.account_id,
        )
        .where(UserRole.user_id == user_id, Permission.code == code)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.first() is not None


async def list_permission_codes_for_user(session: AsyncSession, user_id: uuid.UUID) -> set[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(User, User.id == UserRole.user_id)
        .join(Account, Account.id == User.account_id)
        .where(
            User.status == "ACTIVE",
            Account.status == "ACTIVE",
            UserRole.account_id == User.account_id,
        )
        .where(UserRole.user_id == user_id)
    )
    result = await session.execute(stmt)
    return set(result.scalars().all())
