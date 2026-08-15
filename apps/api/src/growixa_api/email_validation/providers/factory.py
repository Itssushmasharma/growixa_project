import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import decrypt_secret
from growixa_api.billing.repositories import get_account_subscription_with_plan
from growixa_api.email_validation import repositories
from growixa_api.email_validation.providers.base import EmailValidationProvider
from growixa_api.email_validation.providers.clearout_provider import ClearoutProvider


def _build_adapter(*, provider_name: str, api_key: str) -> EmailValidationProvider:
    if provider_name == "CLEAROUT":
        return ClearoutProvider(api_key=api_key)
    raise ValueError(f"Unknown email-validation provider: {provider_name!r}")


async def get_effective_email_validation_provider(
    session: AsyncSession, account_id: uuid.UUID
) -> EmailValidationProvider | None:
    """Resolution (GRX-SAAS-016 follow-up pass, platform-level only -- no per-account
    bring-your-own): returns a real-time vendor adapter only when BOTH the account is on
    a paid plan AND the platform has an active vendor configured. Returns None
    otherwise -- callers fall back to the free syntax/MX/disposable/role checks, never
    an error, so a Free-tier account (or a paid account before any vendor is
    configured) always gets a usable result."""
    subscription = await get_account_subscription_with_plan(session, account_id)
    if subscription is None:
        return None
    _account_subscription, plan = subscription
    if plan.slug == "free":
        return None

    config = await repositories.get_active_platform_config(session)
    if config is None:
        return None

    api_key = decrypt_secret(config.api_key_encrypted)
    return _build_adapter(provider_name=config.provider, api_key=api_key)


async def test_connection(*, provider_name: str, api_key: str) -> None:
    """Builds an adapter from the given (not-yet-saved) credentials and makes one real
    verification call against a known-syntactically-valid test address to confirm the
    key actually works -- nothing is persisted. Same "test before save" convention as
    GRX-EMAIL-012's SMTP test-connection and GRX-AI-005's AI provider test."""
    adapter = _build_adapter(provider_name=provider_name, api_key=api_key)
    await adapter.verify("connection-test@example.com")
