from growixa_api.ai.providers.base import AIGenerationResult, AIModelProvider


class MockAIProvider(AIModelProvider):
    """Deterministic, zero-dependency mock AI provider for testing and offline environments.
    Returns tailored responses for each capability while tracking mock token metrics."""

    def __init__(self, default_response: str | None = None) -> None:
        self.default_response = default_response

    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        if self.default_response:
            return AIGenerationResult(
                text=self.default_response,
                prompt_tokens=len(user_prompt.split()) + 15,
                completion_tokens=len(self.default_response.split()),
                total_tokens=len(user_prompt.split()) + len(self.default_response.split()) + 15,
            )

        lower_prompt = user_prompt.lower()
        lower_system = system_prompt.lower()

        # Capability detection
        if "subject line" in lower_system or "subject" in lower_prompt:
            text = "Transform Your Growth Strategy with Growixa Today"
        elif "cta" in lower_system or "call to action" in lower_system:
            text = "Claim Your Free 14-Day Growth Trial Now"
        elif "ideas" in lower_system or "brainstorm" in lower_system:
            text = (
                "1. 5 Proven Growth Hacks for SaaS Founders\n"
                "2. Why Multi-Channel Marketing Beats Single Channels Every Time\n"
                "3. Case Study: Scaling Lead Generation by 300% in 30 Days"
            )
        elif "linkedin" in lower_system or "linkedin" in lower_prompt:
            text = (
                "Growth doesn't happen by accident—it happens by design.\n\n"
                "Here are 3 core pillars we rely on every day:\n"
                "• Unified customer data across every channel\n"
                "• AI-assisted copywriting tailored to your brand voice\n"
                "• Relentless delivery tracking and optimization\n\n"
                "What strategies are moving the needle for your team this quarter?"
            )
        elif "twitter" in lower_system or "tweet" in lower_prompt:
            text = "Stop guessing your marketing strategy. Automate multi-channel outreach with precision. 🚀"
        elif "repurpose" in lower_system:
            text = (
                "### Email Newsletter Snippet:\n"
                "Discover how unified marketing engines outperform fragmented stacks.\n\n"
                "### Social Post Snippet:\n"
                "Tired of switching between 5 marketing tools? Consolidate and grow faster. #Marketing #SaaS"
            )
        elif "caption" in lower_system:
            text = "Craft high-converting campaigns in minutes with Growixa. Link in bio! ✨"
        elif "rewrite" in lower_system:
            text = "Accelerate your marketing workflow with our automated growth engine."
        elif "hashtags" in lower_system:
            text = "#MarketingAutomation #GrowthHacking #SaaSGrowth #EmailMarketing #B2B"
        elif "posting time" in lower_system:
            text = "Tuesday and Thursday between 9:00 AM and 11:00 AM ET."
        else:
            text = "High-performance marketing copy generated to elevate your brand presence."

        prompt_tokens = max(10, len(user_prompt.split()) + len(system_prompt.split()) // 4)
        completion_tokens = max(5, len(text.split()))
        total_tokens = prompt_tokens + completion_tokens

        return AIGenerationResult(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
