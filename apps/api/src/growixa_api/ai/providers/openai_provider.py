from dataclasses import dataclass
from typing import Any

import httpx

from growixa_api.ai.providers.base import TIMEOUT_SECONDS, AIGenerationResult, AIProviderError

_API_BASE = "https://api.openai.com/v1"


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise AIProviderError(
            f"Non-JSON response from OpenAI (HTTP {response.status_code})"
        ) from exc
    if response.is_error:
        message = data.get("error", {}).get("message", data)
        raise AIProviderError(f"OpenAI returned HTTP {response.status_code}: {message}")
    return data


@dataclass
class OpenAIProvider:
    api_key: str

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{_API_BASE}/chat/completions",
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
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return AIGenerationResult(
            text=choice,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )
