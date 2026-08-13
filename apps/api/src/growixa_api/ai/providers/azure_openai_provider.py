from dataclasses import dataclass
from typing import Any

import httpx

from growixa_api.ai.providers.base import (
    TIMEOUT_SECONDS,
    AIGenerationResult,
    AIProviderError,
    validate_base_url,
)

_API_VERSION = "2024-02-15-preview"


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise AIProviderError(
            f"Non-JSON response from Azure OpenAI (HTTP {response.status_code})"
        ) from exc
    if response.is_error:
        message = data.get("error", {}).get("message", data)
        raise AIProviderError(f"Azure OpenAI returned HTTP {response.status_code}: {message}")
    return data


@dataclass
class AzureOpenAIProvider:
    """`model` in `generate()` is treated as the Azure deployment name -- Azure OpenAI
    routes by deployment, not a raw model identifier, so `default_model` on the owning
    connection row is expected to hold the deployment name."""

    api_key: str
    base_url: str

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        # Re-validated at call time, not only when the connection was saved -- defeats
        # DNS rebinding (DEC-GRX-027).
        validate_base_url(self.base_url)

        url = (
            f"{self.base_url.rstrip('/')}/openai/deployments/{model}/chat/completions"
            f"?api-version={_API_VERSION}"
        )
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    url,
                    headers={"api-key": self.api_key},
                    json={
                        "max_tokens": max_tokens,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
        except httpx.HTTPError as exc:
            raise AIProviderError(str(exc)) from exc

        data = _extract_or_raise(response)
        choice = data["choices"][0]
        text = choice["message"]["content"]
        if not text:
            # Same truncated-before-content failure mode OpenAIProvider guards
            # against (reasoning models can hit max_tokens mid-thought) — surface it
            # as an error rather than silently returning blank text.
            finish_reason = choice.get("finish_reason")
            raise AIProviderError(
                f"Azure OpenAI returned no content (finish_reason={finish_reason!r}) — "
                f"the response may have been truncated before completion; try a "
                f"higher max_tokens"
            )
        usage = data.get("usage", {})
        return AIGenerationResult(
            text=text,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )
