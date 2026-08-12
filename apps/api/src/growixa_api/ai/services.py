import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.ai import repositories
from growixa_api.ai.models import AIProviderConnection
from growixa_api.ai.providers.base import InsecureBaseUrlError, validate_base_url
from growixa_api.ai.schemas import AIProviderConnectionIn
from growixa_api.auth.encryption import encrypt_secret

_BASE_URL_REQUIRED_PROVIDERS = {"AZURE_OPENAI", "OLLAMA"}


class AIProviderConnectionNotFoundError(Exception):
    pass


class MissingBaseUrlError(Exception):
    """Raised when AZURE_OPENAI/OLLAMA is configured with no base_url — both providers
    require a customer/admin-supplied endpoint, unlike OPENAI/ANTHROPIC's fixed one."""


def _validate_connection_input(data: AIProviderConnectionIn) -> None:
    if data.provider in _BASE_URL_REQUIRED_PROVIDERS:
        if not data.base_url:
            raise MissingBaseUrlError(f"{data.provider} requires a base_url")
        # SSRF-safe validation at save time (DEC-GRX-027); re-validated again at call
        # time by the adapter itself, defeating DNS rebinding.
        validate_base_url(data.base_url)


async def list_connections(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[AIProviderConnection]:
    connection = await repositories.get_active_provider_connection(session, account_id)
    return [connection] if connection is not None else []


async def create_connection(
    session: AsyncSession,
    account_id: uuid.UUID,
    data: AIProviderConnectionIn,
    actor_id: uuid.UUID,
) -> AIProviderConnection:
    """Deactivates any existing active connection for this account and creates a new
    row rather than overwriting in place, preserving credential history — same
    convention as email_provider_connections/social_connections. An account brings
    *one* model at a time (DEC-GRX-026), unlike email's per-provider multiplicity."""
    _validate_connection_input(data)
    await repositories.deactivate_active_provider_connections(session, account_id)
    return await repositories.create_provider_connection(
        session,
        {
            "account_id": account_id,
            "provider": data.provider,
            "api_key_encrypted": encrypt_secret(data.api_key) if data.api_key else None,
            "base_url": data.base_url,
            "default_model": data.default_model,
            "created_by_user_id": actor_id,
        },
    )


async def deactivate_connection(
    session: AsyncSession, account_id: uuid.UUID, connection_id: uuid.UUID
) -> AIProviderConnection:
    connection = await repositories.get_provider_connection(session, account_id, connection_id)
    if connection is None:
        raise AIProviderConnectionNotFoundError(f"AI provider connection {connection_id} not found")
    connection.is_active = False
    # Commit + refresh here, not left to the route: onupdate=func.now() columns expire
    # after an UPDATE and raise MissingGreenlet on serialization without an explicit
    # refresh first (same root cause and fix as contacts.services' identical pattern).
    await session.commit()
    await session.refresh(connection)
    return connection


__all__ = [
    "AIProviderConnectionNotFoundError",
    "InsecureBaseUrlError",
    "MissingBaseUrlError",
    "create_connection",
    "deactivate_connection",
    "list_connections",
]
