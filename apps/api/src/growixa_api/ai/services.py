import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.ai import repositories
from growixa_api.ai.capabilities import body_copy, hashtags, posting_time, rewrite, social_caption
from growixa_api.ai.capabilities import subject_line as subject_line_capability
from growixa_api.ai.capabilities import (
    content_ideas,
    content_repurpose,
    cta,
    platform_rewrite,
    tone_rewrite,
)
from growixa_api.ai.capabilities.types import CapabilityInput
from growixa_api.ai.models import AIGeneration, AIProviderConnection, PlatformAIProviderConfig
from growixa_api.ai.providers import factory as factory
from growixa_api.ai.providers.base import AIProviderError, InsecureBaseUrlError, validate_base_url
from growixa_api.ai.providers.factory import AINotConfiguredError, get_effective_ai_provider
from growixa_api.ai.schemas import AIProviderConnectionIn, PlatformAIProviderConfigIn
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.billing.services import check_and_consume_quota
from growixa_api.brand.repositories import get_brand_profile
from growixa_api.pagination import DEFAULT_LIMIT
from growixa_api.usage.models import UsageRecord

_BASE_URL_REQUIRED_PROVIDERS = {"AZURE_OPENAI", "OLLAMA"}

_CAPABILITY_MODULES = {
    "SUBJECT_LINE": subject_line_capability,
    "BODY_COPY": body_copy,
    "SOCIAL_CAPTION": social_caption,
    "REWRITE": rewrite,
    "HASHTAGS": hashtags,
    "POSTING_TIME": posting_time,
    # Phase 5 capabilities (GRX-AI-006)
    "CTA": cta,
    "TONE_REWRITE": tone_rewrite,
    "CONTENT_IDEAS": content_ideas,
    "PLATFORM_REWRITE": platform_rewrite,
    "CONTENT_REPURPOSE": content_repurpose,
}

# Rough, deliberately approximate per-1K-token USD pricing -- good enough for
# "estimated cost" visibility (GRX-AI-006), not billing-grade accuracy. Unknown models
# fall back to a conservative default; Ollama is always $0 (self-hosted, no per-token
# billing).
_APPROX_PRICE_PER_1K_TOKENS_USD: dict[str, float] = {
    "gpt-4o-mini": 0.00026,
    "gpt-4o": 0.0075,
    "claude-sonnet-4-5": 0.009,
    "claude-3-5-haiku": 0.0016,
}
_DEFAULT_PRICE_PER_1K_TOKENS_USD = 0.002


class GenerationFailedError(Exception):
    """Wraps an AIProviderError after it's already been logged as a FAILED
    ai_generations row -- the route maps this to a 502."""


class GenerationNotFoundError(Exception):
    """Raised when a generation ID is not found for the given account."""


class GenerationAlreadyReviewedError(Exception):
    """Raised when trying to approve/reject an already-reviewed generation."""


class GenerationNotApprovableError(Exception):
    """Raised when trying to act on a FAILED generation (no output to approve)."""


def _estimate_cost_usd(*, provider_name: str, model: str, total_tokens: int) -> float:
    if provider_name == "OLLAMA":
        return 0.0
    price_per_1k = _APPROX_PRICE_PER_1K_TOKENS_USD.get(model, _DEFAULT_PRICE_PER_1K_TOKENS_USD)
    return round((total_tokens / 1000) * price_per_1k, 6)


class AIProviderConnectionNotFoundError(Exception):
    pass


class MissingBaseUrlError(Exception):
    """Raised when AZURE_OPENAI/OLLAMA is configured with no base_url — both providers
    require a customer/admin-supplied endpoint, unlike OPENAI/ANTHROPIC's fixed one."""


def _validate_provider_config(*, provider: str, base_url: str | None) -> None:
    """Shared by account BYO connections and the platform default config -- both are
    the same {provider, api_key, base_url, default_model} shape (DEC-GRX-026)."""
    if provider in _BASE_URL_REQUIRED_PROVIDERS and not base_url:
        raise MissingBaseUrlError(f"{provider} requires a base_url")
    if base_url:
        # SSRF-safe validation at save time (DEC-GRX-027) for any custom base_url --
        # required for AZURE_OPENAI/OLLAMA, optional-but-still-validated for OPENAI's
        # OpenAI-compatible-third-party-endpoint override. Re-validated again at call
        # time by the adapter itself, defeating DNS rebinding.
        validate_base_url(base_url)


async def test_connection(
    *, provider: str, api_key: str | None, base_url: str | None, default_model: str
) -> None:
    """Validates credentials via a real, minimal generation call before they're saved
    (or resaved) — nothing is persisted. Shared by the account BYO connection route and
    the platform-admin config route, mirroring integrations/smtp_transport.py's
    test_connection (GRX-EMAIL-012)."""
    _validate_provider_config(provider=provider, base_url=base_url)
    await factory.test_connection(
        provider_name=provider, api_key=api_key, base_url=base_url, model=default_model
    )


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
    _validate_provider_config(provider=data.provider, base_url=data.base_url)
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


async def get_platform_config(session: AsyncSession) -> PlatformAIProviderConfig | None:
    return await repositories.get_active_platform_config(session)


async def set_platform_config(
    session: AsyncSession,
    data: PlatformAIProviderConfigIn,
    actor_platform_admin_id: uuid.UUID,
) -> PlatformAIProviderConfig:
    """Deactivates any existing active platform default and creates a new row —
    same deactivate-then-insert convention as the account-level connection above.
    The first DB-backed, admin-editable platform setting in this codebase
    (DEC-GRX-026)."""
    _validate_provider_config(provider=data.provider, base_url=data.base_url)
    await repositories.deactivate_active_platform_config(session)
    return await repositories.create_platform_config(
        session,
        {
            "provider": data.provider,
            "api_key_encrypted": encrypt_secret(data.api_key) if data.api_key else None,
            "base_url": data.base_url,
            "default_model": data.default_model,
            "created_by_platform_admin_id": actor_platform_admin_id,
        },
    )


async def generate(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    capability: str,
    brief: str,
    existing_text: str | None,
    instruction: str | None,
    linked_entity_type: str | None,
    linked_entity_id: uuid.UUID | None,
) -> AIGeneration:
    """Resolves the effective provider (BYO, else platform default, else
    AINotConfiguredError — DEC-GRX-026), runs the requested capability, and logs the
    result. A provider-call failure still writes a FAILED ai_generations row (provider/
    model are known by then) before raising GenerationFailedError; a resolution
    failure (AINotConfiguredError) never gets that far, since there's no provider/model
    to record yet."""
    resolved = await get_effective_ai_provider(session, account_id)

    # AI-run quota only applies to platform-provided generations -- an account's own
    # bring-your-own key costs Growixa nothing, so it's never metered
    # (BILLING_SYSTEM_ARCHITECTURE.md §4.1, GRX-BILL-005). Checked before the provider
    # call so an over-quota account is blocked before any real platform LLM budget is
    # spent on a call that was never going to be allowed.
    if resolved.source == "PLATFORM_DEFAULT":
        await check_and_consume_quota(session, account_id=account_id, operation="ai_run", qty=1)

    brand_profile = await get_brand_profile(session, account_id)
    capability_input = CapabilityInput(
        brief=brief,
        existing_text=existing_text,
        instruction=instruction,
        brand_voice=brand_profile.brand_voice if brand_profile else None,
    )
    input_context: dict[str, object] = {
        "brief": brief,
        "existing_text": existing_text,
        "instruction": instruction,
    }
    capability_module = _CAPABILITY_MODULES[capability]

    try:
        result = await capability_module.run(capability_input, resolved.provider, resolved.model)
    except AIProviderError as exc:
        await repositories.create_generation(
            session,
            {
                "account_id": account_id,
                "created_by_user_id": actor_id,
                "capability": capability,
                "prompt_template_key": capability_module.PROMPT_TEMPLATE_KEY,
                "input_context": input_context,
                "output": None,
                "provider": resolved.provider_name,
                "model": resolved.model,
                "prompt_tokens": None,
                "completion_tokens": None,
                "estimated_cost_usd": None,
                "status": "FAILED",
                "error_message": str(exc),
                "linked_entity_type": linked_entity_type,
                "linked_entity_id": linked_entity_id,
            },
        )
        await session.commit()
        raise GenerationFailedError(str(exc)) from exc

    total_tokens = result.prompt_tokens + result.completion_tokens
    generation = await repositories.create_generation(
        session,
        {
            "account_id": account_id,
            "created_by_user_id": actor_id,
            "capability": capability,
            "prompt_template_key": capability_module.PROMPT_TEMPLATE_KEY,
            "input_context": input_context,
            "output": {"text": result.text},
            "provider": resolved.provider_name,
            "model": resolved.model,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "estimated_cost_usd": _estimate_cost_usd(
                provider_name=resolved.provider_name,
                model=resolved.model,
                total_tokens=total_tokens,
            ),
            "status": "COMPLETE",
            "error_message": None,
            "linked_entity_type": linked_entity_type,
            "linked_entity_id": linked_entity_id,
        },
    )
    # Fixes a real pre-existing gap: usage_records has had zero writers since Sprint 1
    # (DEC-GRX-007) despite platform_admin's usage view already reading it.
    session.add(
        UsageRecord(
            account_id=account_id,
            operation_type="ai_generation",
            quantity=total_tokens,
            unit="tokens",
            created_by_user_id=actor_id,
            usage_metadata={
                "capability": capability,
                "provider": resolved.provider_name,
                "model": resolved.model,
            },
        )
    )
    await session.commit()
    await session.refresh(generation)
    return generation


async def list_generation_history(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    capability: str | None = None,
    linked_entity_type: str | None = None,
    linked_entity_id: uuid.UUID | None = None,
    approval_status: str | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Sequence[AIGeneration]:
    return await repositories.list_generations(
        session,
        account_id,
        capability=capability,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        approval_status=approval_status,
        limit=limit,
        offset=offset,
    )


async def approve_generation(
    session: AsyncSession,
    account_id: uuid.UUID,
    generation_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    notes: str | None = None,
) -> AIGeneration:
    """Marks a COMPLETE generation as APPROVED by a human manager.
    FAILED generations cannot be approved -- there is no output to approve.
    Already-reviewed generations (APPROVED/REJECTED/EDITED) are idempotency-
    guarded: the caller gets a GenerationAlreadyReviewedError so the route
    can return 409 rather than silently overwriting a prior decision."""
    generation = await repositories.get_generation(session, account_id, generation_id)
    if generation is None:
        raise GenerationNotFoundError(f"AI generation {generation_id} not found")
    if generation.status == "FAILED":
        raise GenerationNotApprovableError("Cannot approve a failed generation.")
    if generation.approval_status in ("APPROVED", "REJECTED", "EDITED"):
        raise GenerationAlreadyReviewedError(
            f"Generation already has approval_status={generation.approval_status!r}"
        )
    generation.approval_status = "APPROVED"
    generation.reviewed_by_user_id = reviewer_id
    generation.reviewed_at = datetime.now(tz=timezone.utc)
    generation.review_notes = notes
    await session.commit()
    await session.refresh(generation)
    return generation


async def reject_generation(
    session: AsyncSession,
    account_id: uuid.UUID,
    generation_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    notes: str | None = None,
) -> AIGeneration:
    """Marks a generation as REJECTED by a human manager. REJECTED generations
    are hidden from the default approval queue but kept for audit purposes."""
    generation = await repositories.get_generation(session, account_id, generation_id)
    if generation is None:
        raise GenerationNotFoundError(f"AI generation {generation_id} not found")
    if generation.approval_status in ("APPROVED", "REJECTED", "EDITED"):
        raise GenerationAlreadyReviewedError(
            f"Generation already has approval_status={generation.approval_status!r}"
        )
    generation.approval_status = "REJECTED"
    generation.reviewed_by_user_id = reviewer_id
    generation.reviewed_at = datetime.now(tz=timezone.utc)
    generation.review_notes = notes
    await session.commit()
    await session.refresh(generation)
    return generation


async def edit_generation_output(
    session: AsyncSession,
    account_id: uuid.UUID,
    generation_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    edited_text: str,
    notes: str | None = None,
) -> AIGeneration:
    """Saves a human-edited version of the AI output to `edited_output` and
    sets approval_status to EDITED. The original `output` is preserved verbatim
    for audit/telemetry (GRX-AI-006). FAILED generations cannot be edited."""
    generation = await repositories.get_generation(session, account_id, generation_id)
    if generation is None:
        raise GenerationNotFoundError(f"AI generation {generation_id} not found")
    if generation.status == "FAILED":
        raise GenerationNotApprovableError("Cannot edit a failed generation.")
    generation.edited_output = {"text": edited_text}
    generation.approval_status = "EDITED"
    generation.reviewed_by_user_id = reviewer_id
    generation.reviewed_at = datetime.now(tz=timezone.utc)
    generation.review_notes = notes
    await session.commit()
    await session.refresh(generation)
    return generation


__all__ = [
    "AIProviderConnectionNotFoundError",
    "AINotConfiguredError",
    "GenerationAlreadyReviewedError",
    "GenerationFailedError",
    "GenerationNotApprovableError",
    "GenerationNotFoundError",
    "InsecureBaseUrlError",
    "MissingBaseUrlError",
    "approve_generation",
    "create_connection",
    "deactivate_connection",
    "edit_generation_output",
    "generate",
    "get_platform_config",
    "list_connections",
    "list_generation_history",
    "reject_generation",
    "set_platform_config",
    "test_connection",
]
