from growixa_api.ai.capabilities.types import CapabilityInput
from growixa_api.ai.prompts.templates import build_social_caption_prompt
from growixa_api.ai.providers.base import AIGenerationResult, AIModelProvider

PROMPT_TEMPLATE_KEY = "social_caption.v1"
# See subject_line.py's identical note on reasoning-model headroom.
MAX_TOKENS = 400


async def run(input: CapabilityInput, provider: AIModelProvider, model: str) -> AIGenerationResult:
    system_prompt, user_prompt = build_social_caption_prompt(input)
    return await provider.generate(
        system_prompt=system_prompt, user_prompt=user_prompt, model=model, max_tokens=MAX_TOKENS
    )
