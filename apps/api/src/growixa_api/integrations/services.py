import secrets
import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.integrations.repositories import (
    create_email_provider_connection,
    create_sender_identity,
    deactivate_active_email_provider_connections,
    get_active_email_provider_connection,
    get_email_provider_connection,
    get_sender_identity,
    list_email_provider_connections,
    list_sender_identities,
    reassign_sender_identities_for_account,
)
from growixa_api.integrations.schemas import (
    EmailProviderConnectionIn,
    EmailProviderConnectionTestIn,
    SenderIdentityIn,
)
from growixa_api.integrations.smtp_transport import test_connection

VALID_VERIFICATION_STATUSES = {"PENDING", "VERIFIED", "FAILED"}


class EmailProviderConnectionNotFoundError(Exception):
    pass


class SenderIdentityNotFoundError(Exception):
    pass


class InvalidVerificationStatusError(Exception):
    pass


async def get_active_connection(
    session: AsyncSession, account_id: uuid.UUID, provider: str
) -> EmailProviderConnection | None:
    return await get_active_email_provider_connection(session, account_id, provider)


async def list_connections(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[EmailProviderConnection]:
    return await list_email_provider_connections(session, account_id)


async def create_connection(
    session: AsyncSession,
    account_id: uuid.UUID,
    data: EmailProviderConnectionIn,
    actor_id: uuid.UUID,
) -> tuple[EmailProviderConnection, str]:
    """Deactivates any existing active connection **for this same account and
    provider** and creates a new row rather than overwriting in place, so the
    credential history isn't silently lost (per DATA_MODEL.md's singleton-by-convention
    note) — since GRX-EMAIL-011, "singleton" means one active connection per provider,
    not one globally, and since GRX-SAAS-001 that's scoped per account too, so a
    different account's or a different provider's active connection is left untouched.

    Also generates this connection's webhook Basic Auth credentials (THREAT_MODEL.md's
    T14) — the plaintext password is returned once, alongside the row, for the API
    layer to include in this one response; it is never persisted or retrievable again.

    Automatically reassigns existing sender identities in this account to the newly
    created active connection so sends and test-sends use the updated credentials.
    """
    existing_connections = await list_email_provider_connections(session, account_id)
    old_ids = [c.id for c in existing_connections if c.provider == data.provider]

    await deactivate_active_email_provider_connections(session, account_id, data.provider)
    webhook_username = secrets.token_urlsafe(12)
    webhook_password = secrets.token_urlsafe(24)
    connection = await create_email_provider_connection(
        session,
        {
            "account_id": account_id,
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

    await reassign_sender_identities_for_account(
        session,
        account_id,
        connection.id,
        old_connection_ids=old_ids if old_ids else None,
    )

    return connection, webhook_password


async def test_email_provider_connection(data: EmailProviderConnectionTestIn) -> None:
    """No session/persistence — validates credentials someone is about to save (or has
    already saved and wants to re-check), never touching `email_provider_connections`.
    Raises EmailSendError (from smtp_transport) on any failure; the caller decides how
    to surface it."""
    await test_connection(
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        smtp_username=data.smtp_username,
        smtp_password=data.smtp_password,
    )


async def list_identities(session: AsyncSession, account_id: uuid.UUID) -> Sequence[SenderIdentity]:
    return await list_sender_identities(session, account_id)


async def create_identity(
    session: AsyncSession,
    account_id: uuid.UUID,
    data: SenderIdentityIn,
    actor_id: uuid.UUID,
) -> SenderIdentity:
    connection = await get_email_provider_connection(
        session, account_id, data.email_provider_connection_id
    )
    if connection is None:
        raise EmailProviderConnectionNotFoundError
    return await create_sender_identity(
        session,
        {
            "account_id": account_id,
            "email_provider_connection_id": data.email_provider_connection_id,
            "from_email": data.from_email,
            "from_name": data.from_name,
            "reply_to_email": data.reply_to_email,
            "created_by_user_id": actor_id,
        },
    )


async def update_identity_verification_status(
    session: AsyncSession,
    account_id: uuid.UUID,
    identity_id: uuid.UUID,
    status: str,
) -> SenderIdentity:
    if status not in VALID_VERIFICATION_STATUSES:
        raise InvalidVerificationStatusError(status)
    identity = await get_sender_identity(session, account_id, identity_id)
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
