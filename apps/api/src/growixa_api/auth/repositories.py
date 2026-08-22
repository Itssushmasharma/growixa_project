import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.models import PasswordResetToken, RefreshToken
from growixa_api.users.models import OAuthIdentity


async def create_refresh_token(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> RefreshToken:
    token = RefreshToken(
        account_id=account_id,
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
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> PasswordResetToken:
    token = PasswordResetToken(
        account_id=account_id, user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
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


async def get_oauth_identity_by_provider_uid(
    session: AsyncSession, provider: str, provider_user_id: str
) -> OAuthIdentity | None:
    result = await session.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == provider,
            OAuthIdentity.provider_user_id == provider_user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_oauth_identity_for_user_and_provider(
    session: AsyncSession, user_id: uuid.UUID, provider: str
) -> OAuthIdentity | None:
    result = await session.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user_id,
            OAuthIdentity.provider == provider,
        )
    )
    return result.scalar_one_or_none()


async def create_oauth_identity(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    provider: str,
    provider_user_id: str,
    email: str,
    avatar_url: str | None = None,
) -> OAuthIdentity:
    identity = OAuthIdentity(
        account_id=account_id,
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        avatar_url=avatar_url,
    )
    session.add(identity)
    await session.flush()
    return identity
