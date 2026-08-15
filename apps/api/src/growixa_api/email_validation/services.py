import asyncio

from growixa_api.email_validation.checks import (
    check_syntax,
    domain_has_mail_exchanger,
    extract_domain,
    extract_local_part,
    is_disposable,
    is_role_account,
)
from growixa_api.email_validation.schemas import EmailValidationResultOut

# Bounds how many concurrent DNS lookups a single bulk request issues -- unbounded
# concurrency across a few thousand rows would hammer the resolver and risk looking like
# abuse to it, not just to us.
_MAX_CONCURRENT_DNS_LOOKUPS = 20

MAX_BULK_ROWS = 2000


def _build_result(email: str, domain: str, has_mx: bool) -> EmailValidationResultOut:
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


async def validate_email(email: str) -> EmailValidationResultOut:
    if not check_syntax(email):
        return EmailValidationResultOut(
            email=email, status="INVALID", reasons=["Malformed email address"]
        )

    domain = extract_domain(email)
    has_mx = await domain_has_mail_exchanger(domain)
    return _build_result(email, domain, has_mx)


async def validate_emails(emails: list[str]) -> list[EmailValidationResultOut]:
    """Batch variant sharing one MX-lookup cache across the whole list -- many rows in a
    real contact CSV share a domain (gmail.com, company.com, ...), so caching by domain
    cuts DNS traffic and wall-clock time substantially versus checking each row alone."""
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
        results.append(_build_result(email, domain, mx_cache.get(domain, False)))

    return results
