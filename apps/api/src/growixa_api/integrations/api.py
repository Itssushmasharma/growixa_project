import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.integrations.schemas import (
    EmailProviderConnectionIn,
    EmailProviderConnectionOut,
    EmailProviderConnectionTestIn,
    SenderIdentityIn,
    SenderIdentityOut,
    SenderIdentityStatusIn,
    SenderIdentityUpdateIn,
)
from growixa_api.integrations.services import (
    ConnectionReferencedBySenderIdentitiesError,
    EmailProviderConnectionNotFoundError,
    InvalidVerificationStatusError,
    SenderIdentityInUseError,
    SenderIdentityNotFoundError,
    create_connection,
    create_identity,
    delete_connection,
    delete_sender_identity_service,
    list_connections,
    list_identities,
    test_email_provider_connection,
    update_identity_connection,
    update_identity_verification_status,
)
from growixa_api.integrations.smtp_transport import EmailSendError
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/integrations", tags=["integrations"])

_require_manage = require_permission("integrations.manage")


@router.get("/email-providers", response_model=list[EmailProviderConnectionOut])
async def list_email_provider_connections_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[EmailProviderConnectionOut]:
    """Lists every configured provider connection (GRX-EMAIL-011: one active row per
    provider now, not a single global one) — the frontend renders one card per known
    provider and looks up its row here, rather than fetching "the" connection."""
    connections = await list_connections(session, account_id)
    return [EmailProviderConnectionOut.model_validate(connection) for connection in connections]


@router.post("/email-providers/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_email_provider_connection_route(
    payload: EmailProviderConnectionTestIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
) -> None:
    """Validates SMTP host/port/credentials by connecting and authenticating only — no
    message is sent, and nothing is persisted. Lets the frontend check a connection
    before (or instead of) saving it."""
    try:
        await test_email_provider_connection(payload)
    except EmailSendError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Connection test failed: {exc}") from exc


@router.post(
    "/email-provider",
    response_model=EmailProviderConnectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_email_provider_connection_route(
    payload: EmailProviderConnectionIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailProviderConnectionOut:
    try:
        connection, webhook_password = await create_connection(
            session, account_id, payload, actor_id
        )
        await session.commit()
    except EmailProviderConnectionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Email provider connection to replace not found"
        ) from exc
    out = EmailProviderConnectionOut.model_validate(connection)
    # Shown once, in this response only — see EmailProviderConnectionOut's docstring.
    return out.model_copy(update={"webhook_password": webhook_password})


@router.delete(
    "/email-providers/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_email_provider_connection_route(
    connection_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Guarded delete (DEC-GRX-035 point 7): deletes a connection if no sender identities
    reference it. Returns 409 naming the blocking identities if any still point to it."""
    try:
        await delete_connection(session, account_id, connection_id)
        await session.commit()
    except EmailProviderConnectionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Email provider connection not found"
        ) from exc
    except ConnectionReferencedBySenderIdentitiesError as exc:
        blocking_emails = ", ".join(i.from_email for i in exc.identities)
        detail = f"Cannot delete connection: referenced by sender identities ({blocking_emails})"
        raise HTTPException(status.HTTP_409_CONFLICT, detail) from exc


@router.get("/sender-identities", response_model=list[SenderIdentityOut])
async def list_sender_identities_route(
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[SenderIdentityOut]:
    identities = await list_identities(session, account_id)
    return [SenderIdentityOut.model_validate(identity) for identity in identities]


@router.post(
    "/sender-identities",
    response_model=SenderIdentityOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_sender_identity_route(
    payload: SenderIdentityIn,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SenderIdentityOut:
    try:
        identity = await create_identity(session, account_id, payload, actor_id)
    except EmailProviderConnectionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Email provider connection not found"
        ) from exc
    await session.commit()
    return SenderIdentityOut.model_validate(identity)


@router.patch("/sender-identities/{identity_id}", response_model=SenderIdentityOut)
async def update_sender_identity_route(
    identity_id: uuid.UUID,
    payload: SenderIdentityUpdateIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SenderIdentityOut:
    try:
        identity = await update_identity_connection(session, account_id, identity_id, payload)
        await session.commit()
        # updated_at's server-side onupdate expires the attribute after an UPDATE commit;
        # a synchronous read of it afterward in the response model triggers an un-awaited
        # lazy reload and raises MissingGreenlet. Refresh explicitly while inside an awaited call.
        await session.refresh(identity)
    except SenderIdentityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender identity not found") from exc
    except EmailProviderConnectionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Email provider connection not found"
        ) from exc
    return SenderIdentityOut.model_validate(identity)


@router.patch("/sender-identities/{identity_id}/status", response_model=SenderIdentityOut)
async def update_sender_identity_status_route(
    identity_id: uuid.UUID,
    payload: SenderIdentityStatusIn,
    _actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> SenderIdentityOut:
    try:
        identity = await update_identity_verification_status(
            session, account_id, identity_id, payload.verification_status
        )
    except SenderIdentityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender identity not found") from exc
    except InvalidVerificationStatusError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid verification status") from exc
    return SenderIdentityOut.model_validate(identity)


@router.delete("/sender-identities/{identity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sender_identity_route(
    identity_id: uuid.UUID,
    actor_id: uuid.UUID = Depends(_require_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await delete_sender_identity_service(session, account_id, identity_id, actor_id)
        await session.commit()
    except SenderIdentityNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender identity not found") from exc
    except SenderIdentityInUseError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            str(exc),
        ) from exc
