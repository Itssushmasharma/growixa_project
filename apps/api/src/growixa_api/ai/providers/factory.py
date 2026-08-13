import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.ai import repositories
from growixa_api.ai.models import AIProviderConnection, PlatformAIProviderConfig
from growixa_api.ai.providers.anthropic_provider import AnthropicProvider
from growixa_api.ai.providers.azure_openai_provider import AzureOpenAIProvider
from growixa_api.ai.providers.base import AIModelProvider
from growixa_api.ai.providers.ollama_provider import OllamaProvider
from growixa_api.ai.providers.openai_provider import OpenAIProvider
from growixa_api.auth.encryption import decrypt_secret


class AINotConfiguredError(Exception):
    """Raised when an account has no active bring-your-own connection and the platform
    has no active default configured either -- surfaced as a clean 409, never a 500 or
    a silent hardcoded fallback to one specific vendor (DEC-GRX-026)."""


@dataclass
class ResolvedAIProvider:
    provider: AIModelProvider
    provider_name: str
    model: str


def _build_adapter(
    *, provider_name: str, api_key: str | None, base_url: str | None
) -> AIModelProvider:
    if provider_name == "OPENAI":
        if api_key is None:
            raise AINotConfiguredError("OpenAI connection is missing its API key")
        return OpenAIProvider(api_key=api_key, base_url=base_url)
    if provider_name == "ANTHROPIC":
        if api_key is None:
            raise AINotConfiguredError("Anthropic connection is missing its API key")
        return AnthropicProvider(api_key=api_key)
    if provider_name == "AZURE_OPENAI":
        if api_key is None or base_url is None:
            raise AINotConfiguredError("Azure OpenAI connection is missing its API key/base_url")
        return AzureOpenAIProvider(api_key=api_key, base_url=base_url)
    if provider_name == "OLLAMA":
        if base_url is None:
            raise AINotConfiguredError("Ollama connection is missing its base_url")
        return OllamaProvider(base_url=base_url, api_key=api_key)
    raise AINotConfiguredError(f"Unknown AI provider: {provider_name!r}")


def _resolve_credentials(
    connection: AIProviderConnection | PlatformAIProviderConfig,
) -> tuple[str | None, str | None]:
    api_key = decrypt_secret(connection.api_key_encrypted) if connection.api_key_encrypted else None
    return api_key, connection.base_url


async def get_effective_ai_provider(
    session: AsyncSession, account_id: uuid.UUID
) -> ResolvedAIProvider:
    """Resolution order (DEC-GRX-026): the account's own active bring-your-own
    connection, else the platform's active default, else AINotConfiguredError."""
    connection = await repositories.get_active_provider_connection(session, account_id)
    if connection is not None:
        api_key, base_url = _resolve_credentials(connection)
        adapter = _build_adapter(
            provider_name=connection.provider, api_key=api_key, base_url=base_url
        )
        return ResolvedAIProvider(
            provider=adapter, provider_name=connection.provider, model=connection.default_model
        )

    platform_config = await repositories.get_active_platform_config(session)
    if platform_config is not None:
        api_key, base_url = _resolve_credentials(platform_config)
        adapter = _build_adapter(
            provider_name=platform_config.provider, api_key=api_key, base_url=base_url
        )
        return ResolvedAIProvider(
            provider=adapter,
            provider_name=platform_config.provider,
            model=platform_config.default_model,
        )

    raise AINotConfiguredError(
        "No AI provider is configured for this account, and the platform has no default "
        "configured either"
    )


async def test_connection(
    *, provider_name: str, api_key: str | None, base_url: str | None, model: str
) -> None:
    """Builds an adapter from the given (not-yet-saved) credentials and makes one real,
    minimal generation call to confirm they actually work -- connects and validates
    only, nothing is persisted. Raises AIProviderError/InsecureBaseUrlError on failure,
    same "test before save" convention as integrations/smtp_transport.py's
    test_connection (GRX-EMAIL-012)."""
    adapter = _build_adapter(provider_name=provider_name, api_key=api_key, base_url=base_url)
    await adapter.generate(
        system_prompt="You are a connection test. Reply with the single word OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_tokens=200,
    )
