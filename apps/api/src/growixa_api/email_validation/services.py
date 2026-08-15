import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.email_validation import repositories
from growixa_api.email_validation.checks import (
    check_syntax,
    domain_has_mail_exchanger,
    extract_domain,
    extract_local_part,
    is_disposable,
    is_role_account,
)
from growixa_api.email_validation.models import PlatformEmailValidationProviderConfig
from growixa_api.email_validation.providers.base import (
    EmailValidationProvider,
    EmailValidationProviderError,
)
from growixa_api.email_validation.schemas import (
    EmailValidationResultOut,
    PlatformEmailValidationProviderConfigIn,
)

# Bounds how many concurrent DNS lookups a single bulk request issues -- unbounded
# concurrency across a few thousand rows would hammer the resolver and risk looking like
# abuse to it, not just to us.
_MAX_CONCURRENT_DNS_LOOKUPS = 20

MAX_BULK_ROWS = 2000


def _build_basic_result(email: str, domain: str, has_mx: bool) -> EmailValidationResultOut:
    if not has_mx:
        return EmailValidationResultOut(
            email=email, status="INVALID", reasons=["Domain has no mail server (no MX/A record)"]
        )
    if is_disposable(domain):
        return EmailValidationResultOut(
            email=email,
            status="DISPOSABLE",
            reasons=["Domain is a known disposable/throwaway provider"],
        )
    if is_role_account(extract_local_part(email)):
        return EmailValidationResultOut(
            email=email,
            status="ROLE",
            reasons=["Address looks like a shared role account, not a person"],
        )
    return EmailValidationResultOut(email=email, status="VALID", reasons=[])


async def _validate_email_basic(email: str) -> EmailValidationResultOut:
    if not check_syntax(email):
        return EmailValidationResultOut(
            email=email, status="INVALID", reasons=["Malformed email address"]
        )

    domain = extract_domain(email)
    has_mx = await domain_has_mail_exchanger(domain)
    return _build_basic_result(email, domain, has_mx)


async def validate_email(
    email: str, *, provider: EmailValidationProvider | None = None
) -> EmailValidationResultOut:
    """When a real-time vendor is resolved for the account (paid plan + an active
    platform config), the vendor's verdict is authoritative and the free checks are
    skipped entirely -- a vendor's mailbox-level classification is a superset of what
    checks.py can determine. If the vendor call itself fails (network error, bad key),
    falls back to the free checks rather than breaking the endpoint for the customer;
    the fallback is noted in the result's reasons so it's visible, not silent."""
    if provider is not None:
        try:
            vendor_result = await provider.verify(email)
            return EmailValidationResultOut(
                email=email,
                status=vendor_result.status,
                reasons=vendor_result.reasons,
                verification_level="REALTIME",
            )
        except EmailValidationProviderError:
            basic_result = await _validate_email_basic(email)
            basic_result.reasons = [
                *basic_result.reasons,
                "Real-time provider was unavailable; showing the basic check instead",
            ]
            return basic_result

    return await _validate_email_basic(email)


async def validate_emails(emails: list[str]) -> list[EmailValidationResultOut]:
    """Batch variant sharing one MX-lookup cache across the whole list -- many rows in a
    real contact CSV share a domain (gmail.com, company.com, ...), so caching by domain
    cuts DNS traffic and wall-clock time substantially versus checking each row alone.
    Bulk CSV stays on the free checks for every account in this pass -- a real-time
    vendor call per row (up to MAX_BULK_ROWS) doesn't match how vendor bulk APIs are
    actually shaped (async job + polling, not a per-row synchronous call); revisit if
    real-time bulk becomes a real ask."""
    syntax_ok: dict[str, bool] = {email: check_syntax(email) for email in emails}
    domains = {extract_domain(email) for email, ok in syntax_ok.items() if ok}

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_DNS_LOOKUPS)

    async def _lookup(domain: str) -> tuple[str, bool]:
        async with semaphore:
            return domain, await domain_has_mail_exchanger(domain)

    lookups = await asyncio.gather(*(_lookup(domain) for domain in domains))
    mx_cache: dict[str, bool] = dict(lookups)

    results: list[EmailValidationResultOut] = []
    for email in emails:
        if not syntax_ok[email]:
            results.append(
                EmailValidationResultOut(
                    email=email, status="INVALID", reasons=["Malformed email address"]
                )
            )
            continue
        domain = extract_domain(email)
        results.append(_build_basic_result(email, domain, mx_cache.get(domain, False)))

    return results


async def get_platform_validation_config(
    session: AsyncSession,
) -> PlatformEmailValidationProviderConfig | None:
    return await repositories.get_active_platform_config(session)


async def set_platform_validation_config(
    session: AsyncSession,
    data: PlatformEmailValidationProviderConfigIn,
    actor_platform_admin_id: uuid.UUID,
) -> PlatformEmailValidationProviderConfig:
    """Deactivates any existing active platform vendor and creates a new row -- same
    deactivate-then-insert convention as PlatformAIProviderConfig/
    PlatformEmailProviderConfig."""
    await repositories.deactivate_active_platform_config(session)
    fields: dict[str, Any] = {
        "provider": data.provider,
        "api_key_encrypted": encrypt_secret(data.api_key),
        "created_by_platform_admin_id": actor_platform_admin_id,
    }
    return await repositories.create_platform_config(session, fields)
