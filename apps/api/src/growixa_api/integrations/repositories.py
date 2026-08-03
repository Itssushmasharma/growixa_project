import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity


async def get_active_email_provider_connection(
    session: AsyncSession,
) -> EmailProviderConnection | None:
    result = await session.execute(
        select(EmailProviderConnection).where(EmailProviderConnection.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def deactivate_all_email_provider_connections(session: AsyncSession) -> None:
    await session.execute(
        update(EmailProviderConnection)
        .where(EmailProviderConnection.is_active.is_(True))
        .values(is_active=False)
    )


async def create_email_provider_connection(
    session: AsyncSession, fields: dict[str, Any]
) -> EmailProviderConnection:
    connection = EmailProviderConnection(**fields)
    session.add(connection)
    await session.flush()
    return connection


async def get_email_provider_connection(
    session: AsyncSession, connection_id: uuid.UUID
) -> EmailProviderConnection | None:
    return await session.get(EmailProviderConnection, connection_id)


async def list_sender_identities(session: AsyncSession) -> Sequence[SenderIdentity]:
    result = await session.execute(select(SenderIdentity).order_by(SenderIdentity.created_at))
    return result.scalars().all()


async def create_sender_identity(session: AsyncSession, fields: dict[str, Any]) -> SenderIdentity:
    identity = SenderIdentity(**fields)
    session.add(identity)
    await session.flush()
    return identity


async def get_sender_identity(
    session: AsyncSession, identity_id: uuid.UUID
) -> SenderIdentity | None:
    return await session.get(SenderIdentity, identity_id)
