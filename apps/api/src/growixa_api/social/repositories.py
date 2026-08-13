import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.social.models import SocialConnection, SocialPost, SocialPostMedia


async def count_active_connections(session: AsyncSession, account_id: uuid.UUID) -> int:
    """Feeds the plan's `max_social_accounts` cap check (`GRX-BILL-005`)."""
    result = await session.execute(
        select(func.count())
        .select_from(SocialConnection)
        .where(SocialConnection.account_id == account_id, SocialConnection.is_active.is_(True))
    )
    return result.scalar_one()


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


async def create_post(session: AsyncSession, fields: dict[str, Any]) -> SocialPost:
    post = SocialPost(**fields)
    session.add(post)
    await session.flush()
    return post


async def get_post(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID
) -> SocialPost | None:
    result = await session.execute(
        select(SocialPost).where(SocialPost.account_id == account_id, SocialPost.id == post_id)
    )
    return result.scalar_one_or_none()


async def list_posts(session: AsyncSession, account_id: uuid.UUID) -> Sequence[SocialPost]:
    result = await session.execute(
        select(SocialPost)
        .where(SocialPost.account_id == account_id)
        .order_by(SocialPost.created_at)
    )
    return result.scalars().all()


async def update_post_fields(
    session: AsyncSession, post: SocialPost, fields: dict[str, Any]
) -> SocialPost:
    for key, value in fields.items():
        setattr(post, key, value)
    await session.flush()
    return post


async def list_post_media(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID
) -> Sequence[SocialPostMedia]:
    result = await session.execute(
        select(SocialPostMedia)
        .where(SocialPostMedia.account_id == account_id, SocialPostMedia.social_post_id == post_id)
        .order_by(SocialPostMedia.position)
    )
    return result.scalars().all()


async def get_post_media(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID, media_id: uuid.UUID
) -> SocialPostMedia | None:
    result = await session.execute(
        select(SocialPostMedia).where(
            SocialPostMedia.account_id == account_id,
            SocialPostMedia.social_post_id == post_id,
            SocialPostMedia.id == media_id,
        )
    )
    return result.scalar_one_or_none()


async def create_post_media(session: AsyncSession, fields: dict[str, Any]) -> SocialPostMedia:
    media = SocialPostMedia(**fields)
    session.add(media)
    await session.flush()
    return media


async def delete_post_media(session: AsyncSession, media: SocialPostMedia) -> None:
    await session.delete(media)
    await session.flush()
