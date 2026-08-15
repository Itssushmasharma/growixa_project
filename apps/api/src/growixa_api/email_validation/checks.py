"""Pure, no-provider email hygiene checks (GRX-SAAS-016, ad hoc).

Deliberately does NOT do real mailbox-existence verification (an SMTP `RCPT TO` probe
against the recipient's own mail server) or catch-all-domain detection -- both require
outbound port-25 connections to arbitrary third-party servers, which most cloud hosts
(including this project's own Hugging Face Space deployment) block or heavily rate-limit,
and which real mail providers throttle/flag as probing behaviour within a handful of
requests. That's the part paid providers (Clearout.io, ZeroBounce) are actually selling;
building it in-house would mean unreliable results plus a real risk of the platform's own
outbound IP getting blacklisted. This module covers the four checks that ARE reliably
free and safe: syntax, MX/A record existence, a static disposable-domain list, and a
role-account local-part list.
"""

import re

import dns.asyncresolver
import dns.exception

# RFC 5322 is far more permissive than real-world addresses need; this simplified pattern
# catches the practical malformed cases (no @, no domain, illegal characters) without
# trying to be a full grammar implementation.
_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")

# A curated (not exhaustive) list of well-known disposable/throwaway email providers.
# A paid provider's live-maintained list runs into the tens of thousands of domains;
# this static list only catches the common, well-known ones -- an accepted limitation
# of the free/no-provider build (see THREAT_MODEL.md's GRX-SAAS-016 ad hoc section).
DISPOSABLE_DOMAINS: frozenset[str] = frozenset(
    {
        "mailinator.com",
        "mailinator2.com",
        "guerrillamail.com",
        "guerrillamail.info",
        "guerrillamail.biz",
        "guerrillamail.de",
        "guerrillamail.net",
        "guerrillamail.org",
        "sharklasers.com",
        "10minutemail.com",
        "10minutemail.net",
        "20minutemail.com",
        "temp-mail.org",
        "tempmail.com",
        "tempmail.net",
        "tempmailo.com",
        "mytemp.email",
        "throwawaymail.com",
        "getnada.com",
        "dispostable.com",
        "fakeinbox.com",
        "maildrop.cc",
        "trashmail.com",
        "trashmail.net",
        "yopmail.com",
        "yopmail.fr",
        "yopmail.net",
        "moakt.com",
        "moakt.cc",
        "emailondeck.com",
        "mintemail.com",
        "spamgourmet.com",
        "mail-temporaire.fr",
        "mohmal.com",
        "mohmal.im",
        "tempinbox.com",
        "fakemailgenerator.com",
        "mailnesia.com",
        "mailcatch.com",
        "throwam.com",
        "burnermail.io",
        "emltmp.com",
        "temp-mail.io",
        "tempr.email",
        "discard.email",
        "discardmail.com",
        "spam4.me",
        "grr.la",
        "inboxbear.com",
        "mailsac.com",
        "tmpmail.org",
        "tmpeml.com",
        "temporary-mail.net",
        "tempail.com",
        "tempm.com",
        "1secmail.com",
        "1secmail.net",
        "1secmail.org",
        "airmail.cc",
        "anonbox.net",
        "crazymailing.com",
        "deadaddress.com",
        "fake-mail.ml",
        "harakirimail.com",
        "jetable.org",
        "meltmail.com",
        "nada.email",
        "spambog.com",
        "spamfree24.org",
        "superrito.com",
        "tempemail.co",
        "tempinbox.co.uk",
        "wegwerfmail.de",
        "zetmail.com",
    }
)

# Local-parts (the part before "@") conventionally used for generic/shared inboxes
# rather than an individual person -- low engagement, not a hard-fail signal.
ROLE_LOCAL_PARTS: frozenset[str] = frozenset(
    {
        "admin",
        "administrator",
        "support",
        "help",
        "helpdesk",
        "info",
        "sales",
        "contact",
        "contactus",
        "marketing",
        "billing",
        "accounts",
        "accounting",
        "abuse",
        "postmaster",
        "hostmaster",
        "webmaster",
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "root",
        "ftp",
        "www",
        "mail",
        "office",
        "careers",
        "jobs",
        "hr",
        "press",
        "media",
        "security",
        "privacy",
        "legal",
        "feedback",
        "newsletter",
        "subscribe",
        "unsubscribe",
        "service",
        "services",
        "team",
        "hello",
        "enquiries",
        "enquiry",
        "inquiries",
        "inquiry",
        "notifications",
        "alerts",
    }
)

_DNS_LIFETIME_SECONDS = 3.0


def check_syntax(email: str) -> bool:
    return bool(_EMAIL_PATTERN.match(email.strip()))


def extract_domain(email: str) -> str:
    return email.strip().rsplit("@", 1)[-1].lower()


def extract_local_part(email: str) -> str:
    return email.strip().rsplit("@", 1)[0].lower()


def is_disposable(domain: str) -> bool:
    return domain.lower() in DISPOSABLE_DOMAINS


def is_role_account(local_part: str) -> bool:
    return local_part.lower() in ROLE_LOCAL_PARTS


async def domain_has_mail_exchanger(domain: str) -> bool:
    """MX lookup with an RFC 5321 §5.1 implicit-MX fallback to A/AAAA -- a domain with no
    explicit MX record but a working A record is still a valid mail-delivery target by
    spec, and skipping the fallback would wrongly flag many correctly-configured small
    domains as INVALID."""
    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = _DNS_LIFETIME_SECONDS
    resolver.timeout = _DNS_LIFETIME_SECONDS

    try:
        answer = await resolver.resolve(domain, "MX")
        return len(answer) > 0
    except dns.exception.DNSException:
        pass

    for record_type in ("A", "AAAA"):
        try:
            answer = await resolver.resolve(domain, record_type)
            if len(answer) > 0:
                return True
        except dns.exception.DNSException:
            continue

    return False
