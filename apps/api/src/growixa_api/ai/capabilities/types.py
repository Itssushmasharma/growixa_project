from dataclasses import dataclass


@dataclass
class CapabilityInput:
    """Shared input shape across capabilities.
    brand_voice and brand_safety_profile are injected from brand_profiles, never client-supplied,
    so they can safely sit alongside the fixed system prompt rather than the untrusted
    user content (THREAT_MODEL.md T56)."""

    brief: str = ""
    existing_text: str | None = None
    instruction: str | None = None
    brand_voice: str | None = None
    channel: str | None = None
    tone: str | None = None
    audience: str | None = None
    length: str | None = None
    brand_safety_profile: object | None = None
