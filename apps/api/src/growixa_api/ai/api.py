import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.ai.providers.base import InsecureBaseUrlError
from growixa_api.ai.schemas import AIProviderConnectionIn, AIProviderConnectionOut
from growixa_api.ai.services import (
    AIProviderConnectionNotFoundError,
    MissingBaseUrlError,
    create_connection,
    deactivate_connection,
    list_connections,
)
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/ai", tags=["ai"])

# BYO connection management reuses integrations.manage (Super-Admin-only) — the same
# class of action as connecting Postmark/Instagram, not a new permission (DEC-GRX-026).
_require_manage = require_permission("integrations.manage")


@router.get("/connections", response_model=list[AIProviderConnectionOut])
async def list_ai_connections_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[AIProviderConnectionOut]:
    connections = await list_connections(session, account_id)
    return [AIProviderConnectionOut.model_validate(connection) for connection in connections]


@router.post(
    "/connections", response_model=AIProviderConnectionOut, status_code=status.HTTP_201_CREATED
)
async def create_ai_connection_route(
    payload: AIProviderConnectionIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> AIProviderConnectionOut:
    try:
        connection = await create_connection(session, account_id, payload, actor_id)
    except (MissingBaseUrlError, InsecureBaseUrlError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    await session.commit()
    return AIProviderConnectionOut.model_validate(connection)


@router.post("/connections/{connection_id}/deactivate", response_model=AIProviderConnectionOut)
async def deactivate_ai_connection_route(
    connection_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> AIProviderConnectionOut:
    try:
        connection = await deactivate_connection(session, account_id, connection_id)
    except AIProviderConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return AIProviderConnectionOut.model_validate(connection)
