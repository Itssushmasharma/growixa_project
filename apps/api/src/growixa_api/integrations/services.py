import secrets
import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.integrations.repositories import (
    create_email_provider_connection,
    create_sender_identity,
    deactivate_all_email_provider_connections,
    get_active_email_provider_connection,
    get_email_provider_connection,
    get_sender_identity,
    list_sender_identities,
)
from growixa_api.integrations.schemas import EmailProviderConnectionIn, SenderIdentityIn

VALID_VERIFICATION_STATUSES = {"PENDING", "VERIFIED", "FAILED"}


class EmailProviderConnectionNotFoundError(Exception):
    pass


class SenderIdentityNotFoundError(Exception):
    pass


class InvalidVerificationStatusError(Exception):
    pass


async def get_active_connection(session: AsyncSession) -> EmailProviderConnection | None:
    return await get_active_email_provider_connection(session)


async def create_connection(
    session: AsyncSession,
    data: EmailProviderConnectionIn,
    actor_id: uuid.UUID,
) -> tuple[EmailProviderConnection, str]:
    """Deactivates any existing active connection and creates a new row rather than
    overwriting in place, so the credential history isn't silently lost (per
    DATA_MODEL.md's singleton-by-convention note).

    Also generates this connection's webhook Basic Auth credentials (THREAT_MODEL.md's
    T14) — the plaintext password is returned once, alongside the row, for the API
    layer to include in this one response; it is never persisted or retrievable again.
    """
    await deactivate_all_email_provider_connections(session)
    webhook_username = secrets.token_urlsafe(12)
    webhook_password = secrets.token_urlsafe(24)
    connection = await create_email_provider_connection(
        session,
        {
            "provider": data.provider,
            "smtp_host": data.smtp_host,
            "smtp_port": data.smtp_port,
            "smtp_username": data.smtp_username,
            "smtp_password_encrypted": encrypt_secret(data.smtp_password),
            "webhook_username": webhook_username,
            "webhook_password_encrypted": encrypt_secret(webhook_password),
            "is_active": True,
            "created_by_user_id": actor_id,
        },
    )
    return connection, webhook_password


async def list_identities(session: AsyncSession) -> Sequence[SenderIdentity]:
    return await list_sender_identities(session)


async def create_identity(
    session: AsyncSession,
    data: SenderIdentityIn,
    actor_id: uuid.UUID,
) -> SenderIdentity:
    connection = await get_email_provider_connection(session, data.email_provider_connection_id)
    if connection is None:
        raise EmailProviderConnectionNotFoundError
    return await create_sender_identity(
        session,
        {
            "email_provider_connection_id": data.email_provider_connection_id,
            "from_email": data.from_email,
            "from_name": data.from_name,
            "reply_to_email": data.reply_to_email,
            "created_by_user_id": actor_id,
        },
    )


async def update_identity_verification_status(
    session: AsyncSession,
    identity_id: uuid.UUID,
    status: str,
) -> SenderIdentity:
    if status not in VALID_VERIFICATION_STATUSES:
        raise InvalidVerificationStatusError(status)
    identity = await get_sender_identity(session, identity_id)
    if identity is None:
        raise SenderIdentityNotFoundError
    identity.verification_status = status
    await session.commit()
    # `updated_at`'s server-side onupdate expires the attribute after an UPDATE commit;
    # a synchronous read of it afterward (e.g. in the API layer's response model) would
    # trigger an un-awaited lazy reload and raise MissingGreenlet. Refresh explicitly
    # while still inside an awaited call.
    await session.refresh(identity)
    return identity
