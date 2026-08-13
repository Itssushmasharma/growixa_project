from growixa_api.ai.capabilities.types import CapabilityInput
from growixa_api.ai.prompts.templates import build_subject_line_prompt
from growixa_api.ai.providers.base import AIGenerationResult, AIModelProvider

PROMPT_TEMPLATE_KEY = "subject_line.v1"
# Generous headroom for reasoning models (e.g. gpt-oss), which spend tokens on an
# internal chain-of-thought before the final answer and can hit a low max_tokens
# mid-thought, leaving no actual content -- a starting point, needs live tuning.
MAX_TOKENS = 400


async def run(input: CapabilityInput, provider: AIModelProvider, model: str) -> AIGenerationResult:
    system_prompt, user_prompt = build_subject_line_prompt(input)
    return await provider.generate(
        system_prompt=system_prompt, user_prompt=user_prompt, model=model, max_tokens=MAX_TOKENS
    )
