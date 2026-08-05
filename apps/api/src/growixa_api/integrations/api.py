import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.integrations.schemas import (
    EmailProviderConnectionIn,
    EmailProviderConnectionOut,
    SenderIdentityIn,
    SenderIdentityOut,
    SenderIdentityStatusIn,
)
from growixa_api.integrations.services import (
    EmailProviderConnectionNotFoundError,
    InvalidVerificationStatusError,
    SenderIdentityNotFoundError,
    create_connection,
    create_identity,
    list_connections,
    list_identities,
    update_identity_verification_status,
)
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/integrations", tags=["integrations"])

_require_manage = require_permission("integrations.manage")


@router.get("/email-providers", response_model=list[EmailProviderConnectionOut])
async def list_email_provider_connections_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> list[EmailProviderConnectionOut]:
    """Lists every configured provider connection (GRX-EMAIL-011: one active row per
    provider now, not a single global one) — the frontend renders one card per known
    provider and looks up its row here, rather than fetching "the" connection."""
    connections = await list_connections(session)
    return [EmailProviderConnectionOut.model_validate(connection) for connection in connections]


@router.post(
    "/email-provider",
    response_model=EmailProviderConnectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_email_provider_connection_route(
    payload: EmailProviderConnectionIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> EmailProviderConnectionOut:
    connection, webhook_password = await create_connection(session, payload, actor_id)
    await session.commit()
    out = EmailProviderConnectionOut.model_validate(connection)
    # Shown once, in this response only — see EmailProviderConnectionOut's docstring.
    return out.model_copy(update={"webhook_password": webhook_password})


@router.get("/sender-identities", response_model=list[SenderIdentityOut])
async def list_sender_identities_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> list[SenderIdentityOut]:
    identities = await list_identities(session)
    return [SenderIdentityOut.model_validate(identity) for identity in identities]


@router.post(
    "/sender-identities",
    response_model=SenderIdentityOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_sender_identity_route(
    payload: SenderIdentityIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> SenderIdentityOut:
    try:
        identity = await create_identity(session, payload, actor_id)
    except EmailProviderConnectionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Email provider connection not found"
        ) from exc
    await session.commit()
    return SenderIdentityOut.model_validate(identity)


@router.patch("/sender-identities/{identity_id}/status", response_model=SenderIdentityOut)
async def update_sender_identity_status_route(
    identity_id: uuid.UUID,
    payload: SenderIdentityStatusIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> SenderIdentityOut:
    try:
        identity = await update_identity_verification_status(
            session, identity_id, payload.verification_status
        )
    except SenderIdentityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender identity not found") from exc
    except InvalidVerificationStatusError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid verification status") from exc
    return SenderIdentityOut.model_validate(identity)
