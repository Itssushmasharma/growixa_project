import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.ai.providers.base import AIProviderError, InsecureBaseUrlError
from growixa_api.ai.providers.factory import AINotConfiguredError
from growixa_api.ai.schemas import (
    AICapability,
    AIGenerationOut,
    AILinkedEntityType,
    AIProviderConnectionIn,
    AIProviderConnectionOut,
    GenerateContentIn,
)
from growixa_api.ai.services import (
    AIProviderConnectionNotFoundError,
    GenerationFailedError,
    MissingBaseUrlError,
    create_connection,
    deactivate_connection,
    generate,
    list_connections,
    list_generation_history,
    test_connection,
)
from growixa_api.db import get_session
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/ai", tags=["ai"])

# BYO connection management reuses integrations.manage (Super-Admin-only) — the same
# class of action as connecting Postmark/Instagram, not a new permission (DEC-GRX-026).
_require_manage = require_permission("integrations.manage")
_require_generate = require_permission("ai.manage")
_require_view = require_permission("ai.view")


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


@router.post("/connections/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_ai_connection_route(
    payload: AIProviderConnectionIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
) -> None:
    """Validates credentials via a real, minimal generation call — nothing is
    persisted. Lets the frontend check a connection before (or instead of) saving it,
    same convention as /integrations/email-providers/test (GRX-EMAIL-012)."""
    try:
        await test_connection(
            provider=payload.provider,
            api_key=payload.api_key,
            base_url=payload.base_url,
            default_model=payload.default_model,
        )
    except (MissingBaseUrlError, InsecureBaseUrlError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Connection test failed: {exc}") from exc


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


@router.post("/generate/{capability}", response_model=AIGenerationOut)
async def generate_content_route(
    capability: AICapability,
    payload: GenerateContentIn,
    actor_id: uuid.UUID = Depends(_require_generate),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> AIGenerationOut:
    """Always assistive — the response is a suggestion for the caller to review and
    insert into a campaign/social post draft, never sent or published automatically
    (DEC-GRX-006). This route has no code path that calls campaigns.send/
    social.publish."""
    try:
        result = await generate(
            session,
            account_id=account_id,
            actor_id=actor_id,
            capability=capability,
            brief=payload.brief,
            existing_text=payload.existing_text,
            instruction=payload.instruction,
            linked_entity_type=payload.linked_entity_type,
            linked_entity_id=payload.linked_entity_id,
        )
    except AINotConfiguredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except GenerationFailedError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Generation failed: {exc}") from exc
    return AIGenerationOut.model_validate(result)


@router.get("/generations", response_model=list[AIGenerationOut])
async def list_ai_generations_route(
    capability: AICapability | None = None,
    linked_entity_type: AILinkedEntityType | None = None,
    linked_entity_id: uuid.UUID | None = None,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[AIGenerationOut]:
    generations = await list_generation_history(
        session,
        account_id,
        capability=capability,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
    )
    return [AIGenerationOut.model_validate(generation) for generation in generations]
