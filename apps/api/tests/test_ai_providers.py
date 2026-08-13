"""AI provider adapter tests (GRX-AI-003) — SSRF validator and call-time re-validation.

Unit-tier: no DB, no app, no network. Matches this codebase's established convention of
never unit-testing a provider client's raw httpx internals directly (no test file exists
for social/instagram_client.py either) — what's tested here is validate_base_url itself
(a pure function) and that each custom-base_url adapter calls it before attempting any
network request, which is verified by giving it an unresolvable/private base_url and
observing InsecureBaseUrlError instead of a network error.
"""

import pytest

from growixa_api.ai.providers.azure_openai_provider import AzureOpenAIProvider
from growixa_api.ai.providers.base import InsecureBaseUrlError, validate_base_url
from growixa_api.ai.providers.ollama_provider import OllamaProvider
from growixa_api.ai.providers.openai_provider import OpenAIProvider


@pytest.mark.parametrize(
    "base_url",
    [
        "http://169.254.169.254/",  # cloud metadata address
        "http://127.0.0.1:11434",  # loopback IP
        "http://localhost:11434",  # loopback hostname
        "http://10.0.0.5:11434",  # private range
        "http://192.168.1.5:11434",  # private range
        "http://172.16.0.1:11434",  # private range
    ],
)
def test_validate_base_url_rejects_non_public_addresses(base_url: str) -> None:
    with pytest.raises(InsecureBaseUrlError):
        validate_base_url(base_url)


def test_validate_base_url_rejects_non_http_scheme() -> None:
    with pytest.raises(InsecureBaseUrlError, match="http or https"):
        validate_base_url("ftp://example.com")


def test_validate_base_url_rejects_unresolvable_hostname() -> None:
    with pytest.raises(InsecureBaseUrlError, match="Could not resolve"):
        validate_base_url("https://this-host-does-not-exist.invalid")


def test_validate_base_url_allows_a_real_public_hostname() -> None:
    # Doesn't raise -- api.openai.com resolves to a real public address.
    validate_base_url("https://api.openai.com")


@pytest.mark.asyncio
async def test_azure_provider_revalidates_base_url_at_call_time() -> None:
    """Even if a connection was saved with a base_url that validated fine at the time,
    generate() must re-check it (DEC-GRX-027) -- simulated here by constructing the
    adapter directly with a now-private base_url and confirming it's rejected before
    any HTTP call is attempted (no network mock needed since it never gets that far)."""
    provider = AzureOpenAIProvider(api_key="fake", base_url="http://169.254.169.254/")
    with pytest.raises(InsecureBaseUrlError):
        await provider.generate(
            system_prompt="system", user_prompt="user", model="gpt-4", max_tokens=10
        )


@pytest.mark.asyncio
async def test_ollama_provider_revalidates_base_url_at_call_time() -> None:
    provider = OllamaProvider(base_url="http://127.0.0.1:11434")
    with pytest.raises(InsecureBaseUrlError):
        await provider.generate(
            system_prompt="system", user_prompt="user", model="llama3", max_tokens=10
        )


@pytest.mark.asyncio
async def test_openai_provider_validates_a_custom_base_url_override() -> None:
    """OpenAIProvider's base_url is optional (defaults to the official endpoint) but is
    still SSRF-validated whenever a custom one is actually supplied (e.g. an
    OpenAI-compatible third-party API)."""
    provider = OpenAIProvider(api_key="fake", base_url="http://192.168.1.1/v1")
    with pytest.raises(InsecureBaseUrlError):
        await provider.generate(
            system_prompt="system", user_prompt="user", model="gpt-4", max_tokens=10
        )
