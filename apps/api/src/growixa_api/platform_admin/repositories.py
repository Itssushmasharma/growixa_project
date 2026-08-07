import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import Account
from growixa_api.users.models import User


async def list_accounts(session: AsyncSession) -> Sequence[Account]:
    result = await session.execute(select(Account).order_by(Account.created_at))
    return result.scalars().all()


async def get_account_by_id(session: AsyncSession, account_id: uuid.UUID) -> Account | None:
    return await session.get(Account, account_id)


async def count_users_by_account(session: AsyncSession) -> dict[uuid.UUID, int]:
    stmt = select(User.account_id, func.count(User.id)).group_by(User.account_id)
    result = await session.execute(stmt)
    return {account_id: count for account_id, count in result.all()}
