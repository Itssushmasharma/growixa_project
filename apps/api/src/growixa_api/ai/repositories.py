import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.ai.models import AIGeneration, AIProviderConnection, PlatformAIProviderConfig
from growixa_api.pagination import DEFAULT_LIMIT


async def get_active_provider_connection(
    session: AsyncSession, account_id: uuid.UUID
) -> AIProviderConnection | None:
    result = await session.execute(
        select(AIProviderConnection).where(
            AIProviderConnection.account_id == account_id,
            AIProviderConnection.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def get_provider_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> AIProviderConnection | None:
    result = await session.execute(
        select(AIProviderConnection).where(
            AIProviderConnection.account_id == account_id,
            AIProviderConnection.id == connection_id,
        )
    )
    return result.scalar_one_or_none()


async def deactivate_active_provider_connections(
    session: AsyncSession, account_id: uuid.UUID
) -> None:
    await session.execute(
        update(AIProviderConnection)
        .where(
            AIProviderConnection.account_id == account_id,
            AIProviderConnection.is_active.is_(True),
        )
        .values(is_active=False)
    )


async def create_provider_connection(
    session: AsyncSession, fields: dict[str, Any]
) -> AIProviderConnection:
    connection = AIProviderConnection(**fields)
    session.add(connection)
    await session.flush()
    return connection


async def get_active_platform_config(
    session: AsyncSession,
) -> PlatformAIProviderConfig | None:
    result = await session.execute(
        select(PlatformAIProviderConfig).where(PlatformAIProviderConfig.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def deactivate_active_platform_config(session: AsyncSession) -> None:
    await session.execute(
        update(PlatformAIProviderConfig)
        .where(PlatformAIProviderConfig.is_active.is_(True))
        .values(is_active=False)
    )


async def create_platform_config(
    session: AsyncSession, fields: dict[str, Any]
) -> PlatformAIProviderConfig:
    config = PlatformAIProviderConfig(**fields)
    session.add(config)
    await session.flush()
    return config


async def create_generation(session: AsyncSession, fields: dict[str, Any]) -> AIGeneration:
    generation = AIGeneration(**fields)
    session.add(generation)
    await session.flush()
    return generation


async def get_generation(
    session: AsyncSession, account_id: uuid.UUID, generation_id: uuid.UUID
) -> AIGeneration | None:
    result = await session.execute(
        select(AIGeneration).where(
            AIGeneration.account_id == account_id, AIGeneration.id == generation_id
        )
    )
    return result.scalar_one_or_none()


async def list_generations(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    capability: str | None = None,
    linked_entity_type: str | None = None,
    linked_entity_id: uuid.UUID | None = None,
    approval_status: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Sequence[AIGeneration]:
    query = select(AIGeneration).where(AIGeneration.account_id == account_id)
    if capability is not None:
        query = query.where(AIGeneration.capability == capability)
    if linked_entity_type is not None:
        query = query.where(AIGeneration.linked_entity_type == linked_entity_type)
    if linked_entity_id is not None:
        query = query.where(AIGeneration.linked_entity_id == linked_entity_id)
    if approval_status is not None:
        query = query.where(AIGeneration.approval_status == approval_status)
    query = query.order_by(AIGeneration.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return result.scalars().all()
