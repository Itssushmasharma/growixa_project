import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity


async def get_active_email_provider_connection(
    session: AsyncSession, account_id: uuid.UUID, provider: str
) -> EmailProviderConnection | None:
    result = await session.execute(
        select(EmailProviderConnection).where(
            EmailProviderConnection.account_id == account_id,
            EmailProviderConnection.provider == provider,
            EmailProviderConnection.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def list_active_email_provider_connections(
    session: AsyncSession, provider: str
) -> Sequence[EmailProviderConnection]:
    """Unscoped by account -- the sole caller is the Postmark webhook receiver, which has
    no account context of its own (`/webhooks/postmark` carries no account identifier;
    Postmark authenticates via this connection's own webhook Basic Auth credentials
    instead). It must check the incoming credentials against every account's active
    connection for this provider to find out which account they belong to."""
    result = await session.execute(
        select(EmailProviderConnection).where(
            EmailProviderConnection.provider == provider,
            EmailProviderConnection.is_active.is_(True),
        )
    )
    return result.scalars().all()


async def deactivate_active_email_provider_connections(
    session: AsyncSession, account_id: uuid.UUID, provider: str
) -> None:
    await session.execute(
        update(EmailProviderConnection)
        .where(
            EmailProviderConnection.account_id == account_id,
            EmailProviderConnection.provider == provider,
            EmailProviderConnection.is_active.is_(True),
        )
        .values(is_active=False)
    )


async def list_email_provider_connections(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[EmailProviderConnection]:
    result = await session.execute(
        select(EmailProviderConnection)
        .where(
            EmailProviderConnection.account_id == account_id,
            EmailProviderConnection.is_active.is_(True),
        )
        .order_by(EmailProviderConnection.created_at)
    )
    return result.scalars().all()


async def create_email_provider_connection(
    session: AsyncSession, fields: dict[str, Any]
) -> EmailProviderConnection:
    connection = EmailProviderConnection(**fields)
    session.add(connection)
    await session.flush()
    return connection


async def get_email_provider_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> EmailProviderConnection | None:
    result = await session.execute(
        select(EmailProviderConnection).where(
            EmailProviderConnection.account_id == account_id,
            EmailProviderConnection.id == connection_id,
        )
    )
    return result.scalar_one_or_none()


async def list_sender_identities(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SenderIdentity]:
    result = await session.execute(
        select(SenderIdentity)
        .where(SenderIdentity.account_id == account_id)
        .order_by(SenderIdentity.created_at)
    )
    return result.scalars().all()


async def create_sender_identity(session: AsyncSession, fields: dict[str, Any]) -> SenderIdentity:
    identity = SenderIdentity(**fields)
    session.add(identity)
    await session.flush()
    return identity


async def get_sender_identity(
    session: AsyncSession, account_id: uuid.UUID, identity_id: uuid.UUID
) -> SenderIdentity | None:
    result = await session.execute(
        select(SenderIdentity).where(
            SenderIdentity.account_id == account_id, SenderIdentity.id == identity_id
        )
    )
    return result.scalar_one_or_none()


async def list_sender_identities_referencing_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> Sequence[SenderIdentity]:
    result = await session.execute(
        select(SenderIdentity).where(
            SenderIdentity.account_id == account_id,
            SenderIdentity.email_provider_connection_id == connection_id,
        )
    )
    return result.scalars().all()


async def deactivate_email_provider_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> None:
    await session.execute(
        update(EmailProviderConnection)
        .where(
            EmailProviderConnection.account_id == account_id,
            EmailProviderConnection.id == connection_id,
            EmailProviderConnection.is_active.is_(True),
        )
        .values(is_active=False)
    )


async def delete_email_provider_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> None:
    await session.execute(
        delete(EmailProviderConnection).where(
            EmailProviderConnection.account_id == account_id,
            EmailProviderConnection.id == connection_id,
        )
    )


async def update_sender_identity(
    session: AsyncSession,
    account_id: uuid.UUID,
    identity_id: uuid.UUID,
    fields: dict[str, Any],
) -> SenderIdentity | None:
    identity = await get_sender_identity(session, account_id, identity_id)
    if identity is None:
        return None
    for key, value in fields.items():
        setattr(identity, key, value)
    await session.flush()
    return identity


async def reassign_sender_identities_for_account(
    session: AsyncSession,
    account_id: uuid.UUID,
    new_connection_id: uuid.UUID,
    old_connection_ids: Sequence[uuid.UUID] | None = None,
) -> None:
    """Reassigns sender identities in this account to the newly active connection.
    If old_connection_ids is provided, reassigns only identities referencing those connections;
    otherwise reassigns all identities in the account."""
    stmt = (
        update(SenderIdentity)
        .where(SenderIdentity.account_id == account_id)
        .values(email_provider_connection_id=new_connection_id)
    )
    if old_connection_ids:
        stmt = stmt.where(SenderIdentity.email_provider_connection_id.in_(old_connection_ids))
    await session.execute(stmt)


async def list_campaigns_referencing_sender_identity(
    session: AsyncSession, account_id: uuid.UUID, identity_id: uuid.UUID
) -> Sequence[Any]:
    from growixa_api.campaigns.models import Campaign

    result = await session.execute(
        select(Campaign).where(
            Campaign.account_id == account_id,
            Campaign.sender_identity_id == identity_id,
        )
    )
    return result.scalars().all()


async def delete_sender_identity(
    session: AsyncSession, account_id: uuid.UUID, identity_id: uuid.UUID
) -> None:
    await session.execute(
        delete(SenderIdentity).where(
            SenderIdentity.account_id == account_id,
            SenderIdentity.id == identity_id,
        )
    )
