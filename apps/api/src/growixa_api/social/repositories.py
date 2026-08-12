import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.social.models import SocialConnection


async def get_active_connection(
    session: AsyncSession, account_id: uuid.UUID, provider: str
) -> SocialConnection | None:
    result = await session.execute(
        select(SocialConnection).where(
            SocialConnection.account_id == account_id,
            SocialConnection.provider == provider,
            SocialConnection.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def list_connections(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SocialConnection]:
    result = await session.execute(
        select(SocialConnection)
        .where(SocialConnection.account_id == account_id)
        .order_by(SocialConnection.provider)
    )
    return result.scalars().all()


async def get_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> SocialConnection | None:
    result = await session.execute(
        select(SocialConnection).where(
            SocialConnection.account_id == account_id, SocialConnection.id == connection_id
        )
    )
    return result.scalar_one_or_none()


async def deactivate_active_connections(
    session: AsyncSession, account_id: uuid.UUID, provider: str
) -> None:
    await session.execute(
        update(SocialConnection)
        .where(
            SocialConnection.account_id == account_id,
            SocialConnection.provider == provider,
            SocialConnection.is_active.is_(True),
        )
        .values(is_active=False)
    )


async def create_connection(session: AsyncSession, fields: dict[str, Any]) -> SocialConnection:
    connection = SocialConnection(**fields)
    session.add(connection)
    await session.flush()
    return connection
