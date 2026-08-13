from dataclasses import dataclass
from typing import Any

import httpx

from growixa_api.ai.providers.base import (
    TIMEOUT_SECONDS,
    AIGenerationResult,
    AIProviderError,
    validate_base_url,
)


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise AIProviderError(
            f"Non-JSON response from Ollama (HTTP {response.status_code})"
        ) from exc
    if response.is_error:
        raise AIProviderError(f"Ollama returned HTTP {response.status_code}: {data}")
    return data


@dataclass
class OllamaProvider:
    """Self-hosted Ollama typically needs no API key -- `api_key` is optional and, if
    set, sent as a bearer token for the common case of a customer proxying their Ollama
    instance behind their own auth."""

    base_url: str
    api_key: str | None = None

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        # Re-validated at call time, not only when the connection was saved -- defeats
        # DNS rebinding (DEC-GRX-027).
        validate_base_url(self.base_url)

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/api/chat",
                    headers=headers,
                    json={
                        "model": model,
                        "stream": False,
                        "options": {"num_predict": max_tokens},
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
        except httpx.HTTPError as exc:
            raise AIProviderError(str(exc)) from exc

        data = _extract_or_raise(response)
        text = str(data.get("message", {}).get("content", ""))
        if not text:
            raise AIProviderError(
                f"Ollama returned no content (done_reason={data.get('done_reason')!r}) "
                f"— the response may have been truncated before completion; try a "
                f"higher max_tokens"
            )
        return AIGenerationResult(
            text=text,
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            completion_tokens=int(data.get("eval_count", 0)),
        )
