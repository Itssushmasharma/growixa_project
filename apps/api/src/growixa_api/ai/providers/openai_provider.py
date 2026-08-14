from dataclasses import dataclass
from typing import Any

import httpx

from growixa_api.ai.providers.base import (
    TIMEOUT_SECONDS,
    AIGenerationResult,
    AIProviderError,
    validate_base_url,
)

_DEFAULT_API_BASE = "https://api.openai.com/v1"


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise AIProviderError(
            f"Non-JSON response from OpenAI (HTTP {response.status_code})"
        ) from exc
    if response.is_error:
        err = data.get("error") if isinstance(data, dict) else str(data)
        if isinstance(err, dict):
            message = err.get("message", str(data))
        elif isinstance(err, str):
            message = err
        else:
            message = str(data)
        raise AIProviderError(f"OpenAI returned HTTP {response.status_code}: {message}")
    return data


@dataclass
class OpenAIProvider:
    """`base_url` is optional and defaults to OpenAI's own official endpoint — set it to
    point at any OpenAI-compatible third-party API instead (e.g. a provider offering the
    same /chat/completions wire format at their own domain). SSRF-validated the same as
    Azure/Ollama's custom base_url whenever it's actually overridden (DEC-GRX-027)."""

    api_key: str
    base_url: str | None = None

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        api_base = _DEFAULT_API_BASE
        if self.base_url:
            validate_base_url(self.base_url)
            api_base = self.base_url.rstrip("/")

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": model,
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
        msg = choice.get("message", {})
        text = msg.get("content") or msg.get("reasoning_content") or msg.get("reasoning")
        if not text:
            finish_reason = choice.get("finish_reason")
            raise AIProviderError(
                f"OpenAI-compatible provider returned no content (finish_reason="
                f"{finish_reason!r}) — the response may have been truncated before "
                f"completion; try a higher max_tokens"
            )
        usage = data.get("usage", {})
        return AIGenerationResult(
            text=text,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )
