from dataclasses import dataclass
from typing import Any

import httpx

from growixa_api.ai.providers.base import TIMEOUT_SECONDS, AIGenerationResult, AIProviderError

_API_BASE = "https://api.anthropic.com/v1"
_ANTHROPIC_VERSION = "2023-06-01"


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise AIProviderError(
            f"Non-JSON response from Anthropic (HTTP {response.status_code})"
        ) from exc
    if response.is_error:
        message = data.get("error", {}).get("message", data)
        raise AIProviderError(f"Anthropic returned HTTP {response.status_code}: {message}")
    return data


@dataclass
class AnthropicProvider:
    api_key: str

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{_API_BASE}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": _ANTHROPIC_VERSION,
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                )
        except httpx.HTTPError as exc:
            raise AIProviderError(str(exc)) from exc

        data = _extract_or_raise(response)
        text = "".join(block.get("text", "") for block in data.get("content", []))
        if not text:
            raise AIProviderError(
                f"Anthropic returned no content (stop_reason={data.get('stop_reason')!r}) "
                f"— the response may have been truncated before completion; try a "
                f"higher max_tokens"
            )
        usage = data.get("usage", {})
        return AIGenerationResult(
            text=text,
            prompt_tokens=int(usage.get("input_tokens", 0)),
            completion_tokens=int(usage.get("output_tokens", 0)),
        )
