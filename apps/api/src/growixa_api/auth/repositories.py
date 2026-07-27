import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.models import PasswordResetToken, RefreshToken


async def create_refresh_token(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    session.add(token)
    await session.flush()
    return token


async def get_refresh_token_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def list_active_refresh_tokens_for_user(
    session: AsyncSession, user_id: uuid.UUID
) -> Sequence[RefreshToken]:
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    )
    return result.scalars().all()


async def create_password_reset_token(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> PasswordResetToken:
    token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    session.add(token)
    await session.flush()
    return token


async def get_password_reset_token_by_hash(
    session: AsyncSession, token_hash: str
) -> PasswordResetToken | None:
    result = await session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()
