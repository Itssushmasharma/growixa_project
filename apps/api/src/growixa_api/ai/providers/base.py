import ipaddress
import socket
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

TIMEOUT_SECONDS = 30.0


class AIProviderError(Exception):
    """Wraps any failure talking to an AI provider (network, or a provider-returned
    error payload) behind one type, mirroring InstagramApiError/EmailSendError's shape."""


class InsecureBaseUrlError(AIProviderError):
    """Raised when a custom base_url fails SSRF-safe validation (DEC-GRX-027)."""


@dataclass
class AIGenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int


class AIModelProvider(Protocol):
    """Adapter interface named in DEC-GRX-005. One concrete implementation per vendor
    (openai_provider.py / azure_openai_provider.py / anthropic_provider.py /
    ollama_provider.py); resolved per account by providers/factory.py."""

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult: ...


def validate_base_url(base_url: str) -> None:
    """SSRF-safe validation for a custom AI provider base_url (DEC-GRX-027, THREAT_MODEL.md
    T52/T53). Applied uniformly to both platform-admin and customer-supplied values, at
    both connection-save time and again at the top of every azure_openai_provider.py /
    ollama_provider.py `generate()` call -- the call-time re-check is what defeats DNS
    rebinding (a hostname that resolves safely when saved, but not by the time it's
    actually called).

    Rejects non-http(s) schemes and any hostname that resolves to a private, loopback,
    link-local, multicast, reserved, or unspecified address -- this already covers the
    169.254.169.254 cloud metadata address (link-local range) without a separate check.

    Redirects are handled by never following them: every provider adapter's own httpx
    call leaves `follow_redirects` at its default (False), so a 3xx response is surfaced
    as a plain AIProviderError rather than silently chased to an unvalidated target
    (THREAT_MODEL.md T54) -- no legitimate chat/completions API redirects.
    """
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https"):
        raise InsecureBaseUrlError(f"base_url must use http or https, got: {parsed.scheme!r}")
    hostname = parsed.hostname
    if not hostname:
        raise InsecureBaseUrlError("base_url has no hostname")
    _validate_hostname_resolves_publicly(hostname)


def _validate_hostname_resolves_publicly(hostname: str) -> None:
    try:
        # Resolve every address this hostname could return -- reject if ANY of them is
        # non-public, since DNS can return multiple records and an attacker only needs
        # one to land privately.
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise InsecureBaseUrlError(f"Could not resolve base_url hostname: {hostname}") from exc

    for _family, _type, _proto, _canonname, sockaddr in addr_infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise InsecureBaseUrlError(
                f"base_url hostname {hostname!r} resolves to a non-public address ({ip})"
            )
