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
    get_active_connection,
    list_identities,
    update_identity_verification_status,
)
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/integrations", tags=["integrations"])

_require_manage = require_permission("integrations.manage")


@router.get("/email-provider", response_model=EmailProviderConnectionOut | None)
async def read_email_provider_connection(
    _actor_id: uuid.UUID = Depends(_require_manage),
    session: AsyncSession = Depends(get_session),
) -> EmailProviderConnectionOut | None:
    connection = await get_active_connection(session)
    return EmailProviderConnectionOut.model_validate(connection) if connection is not None else None


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
    connection = await create_connection(session, payload, actor_id)
    await session.commit()
    return EmailProviderConnectionOut.model_validate(connection)


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
