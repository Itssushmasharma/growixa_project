import ipaddress
import re
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


# Pricing rates per 1k tokens: (prompt_cost_usd, completion_cost_usd)
MODEL_PRICING_PER_1K: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    # Anthropic
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-5-haiku": (0.0008, 0.004),
    "claude-3-opus": (0.015, 0.075),
    # Default fallback
    "default": (0.0005, 0.0015),
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates estimated cost in USD based on model pricing matrix."""
    model_lower = model.lower()
    rates = MODEL_PRICING_PER_1K["default"]
    for key, val in MODEL_PRICING_PER_1K.items():
        if key in model_lower:
            rates = val
            break
    prompt_rate, completion_rate = rates
    cost = (prompt_tokens / 1000.0 * prompt_rate) + (completion_tokens / 1000.0 * completion_rate)
    return round(cost, 6)


_SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(bearer\s+[a-zA-Z0-9_\-\.]{16,})"), "[REDACTED_AUTH_TOKEN]"),
    (re.compile(r"(?i)(sk-[a-zA-Z0-9]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(xox[baprs]-[a-zA-Z0-9_\-]{10,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD_NUMBER]"),
    (re.compile(r"(?i)(password\s*[:=]\s*['\"]?[^\s'\"]+)"), "password=[REDACTED]"),
]


def sanitize_sensitive_input(text: str) -> str:
    """Scrubs sensitive credentials and credit cards before passing to third-party AI APIs."""
    if not text:
        return text
    sanitized = text
    for pattern, replacement in _SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


@dataclass
class AIGenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class AIModelProvider(Protocol):
    """Adapter interface named in DEC-GRX-005. One concrete implementation per vendor
    (openai_provider.py / azure_openai_provider.py / anthropic_provider.py /
    ollama_provider.py / mock_provider.py); resolved per account by providers/factory.py."""

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
