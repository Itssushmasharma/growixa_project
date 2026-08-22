import secrets
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.integrations.repositories import (
    create_email_provider_connection,
    create_sender_identity,
    deactivate_active_email_provider_connections,
    deactivate_email_provider_connection,
    delete_email_provider_connection,
    get_active_email_provider_connection,
    get_email_provider_connection,
    get_sender_identity,
    list_email_provider_connections,
    list_sender_identities,
    list_sender_identities_referencing_connection,
    reassign_sender_identities_for_account,
    update_sender_identity,
)
from growixa_api.integrations.schemas import (
    EmailProviderConnectionIn,
    EmailProviderConnectionTestIn,
    SenderIdentityIn,
    SenderIdentityUpdateIn,
)
from growixa_api.integrations.smtp_transport import test_connection

VALID_VERIFICATION_STATUSES = {"PENDING", "VERIFIED", "FAILED"}


class EmailProviderConnectionNotFoundError(Exception):
    pass


class SenderIdentityNotFoundError(Exception):
    pass


class InvalidVerificationStatusError(Exception):
    pass


class ConnectionReferencedBySenderIdentitiesError(Exception):
    def __init__(self, identities: Sequence[SenderIdentity]) -> None:
        self.identities = identities
        super().__init__(
            f"Cannot delete connection: referenced by {len(identities)} sender identities"
        )


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
    """Creates a new active email provider connection (DEC-GRX-035).

    - POSTMARK: preserves single-active-connection rule per account; deactivates any existing
      active POSTMARK connection and reassigns its identities to the new connection.
    - CUSTOM_SMTP: multiple active connections are allowed.
      If replacing_connection_id is specified (e.g. replacing a specific relay), deactivates
      only that connection and reassigns ONLY the identities that referenced it.
      If replacing_connection_id is None (adding an additional relay), no existing connection
      is deactivated and no existing identities are reassigned.
    """
    reassign_old_ids: list[uuid.UUID] | None = None

    if data.provider == "POSTMARK":
        existing_connections = await list_email_provider_connections(session, account_id)
        old_ids = [c.id for c in existing_connections if c.provider == "POSTMARK" and c.is_active]
        await deactivate_active_email_provider_connections(session, account_id, "POSTMARK")
        if old_ids:
            reassign_old_ids = old_ids
    else:
        if data.replacing_connection_id is not None:
            old_conn = await get_email_provider_connection(
                session, account_id, data.replacing_connection_id
            )
            if old_conn is not None and old_conn.is_active:
                await deactivate_email_provider_connection(
                    session, account_id, data.replacing_connection_id
                )
                reassign_old_ids = [data.replacing_connection_id]

    webhook_username = secrets.token_urlsafe(12)
    webhook_password = secrets.token_urlsafe(24)
    connection = await create_email_provider_connection(
        session,
        {
            "account_id": account_id,
            "name": data.name,
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

    if reassign_old_ids:
        await reassign_sender_identities_for_account(
            session,
            account_id,
            connection.id,
            old_connection_ids=reassign_old_ids,
        )

    return connection, webhook_password


async def delete_connection(
    session: AsyncSession,
    account_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> None:
    """Guarded delete (DEC-GRX-035 point 7): refuses deletion if any sender identities
    still reference this connection, returning the blocking identities."""
    connection = await get_email_provider_connection(session, account_id, connection_id)
    if connection is None:
        raise EmailProviderConnectionNotFoundError

    referencing_identities = await list_sender_identities_referencing_connection(
        session, account_id, connection_id
    )
    if referencing_identities:
        raise ConnectionReferencedBySenderIdentitiesError(referencing_identities)

    await delete_email_provider_connection(session, account_id, connection_id)


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


async def update_identity_connection(
    session: AsyncSession,
    account_id: uuid.UUID,
    identity_id: uuid.UUID,
    payload: SenderIdentityUpdateIn,
) -> SenderIdentity:
    identity = await get_sender_identity(session, account_id, identity_id)
    if identity is None:
        raise SenderIdentityNotFoundError

    fields: dict[str, Any] = {}
    if payload.email_provider_connection_id is not None:
        target_conn = await get_email_provider_connection(
            session, account_id, payload.email_provider_connection_id
        )
        if target_conn is None:
            raise EmailProviderConnectionNotFoundError
        fields["email_provider_connection_id"] = payload.email_provider_connection_id

    if payload.from_name is not None:
        fields["from_name"] = payload.from_name
    if payload.reply_to_email is not None:
        fields["reply_to_email"] = payload.reply_to_email

    updated = await update_sender_identity(session, account_id, identity_id, fields)
    if updated is None:
        raise SenderIdentityNotFoundError
    return updated


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
    await session.refresh(identity)
    return identity
