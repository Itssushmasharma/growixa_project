import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.accounts.models import AccountVerificationToken
from growixa_api.users.models import User


async def get_account_id_for_user(session: AsyncSession, user_id: uuid.UUID) -> uuid.UUID | None:
    result = await session.execute(select(User.account_id).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_account_verification_token(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> AccountVerificationToken:
    token = AccountVerificationToken(
        account_id=account_id, user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
    session.add(token)
    await session.flush()
    return token


async def get_account_verification_token_by_hash(
    session: AsyncSession, token_hash: str
) -> AccountVerificationToken | None:
    result = await session.execute(
        select(AccountVerificationToken).where(AccountVerificationToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()
