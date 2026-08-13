from dataclasses import dataclass


@dataclass
class CapabilityInput:
    """Shared input shape across all six capabilities — not every field is used by
    every one (REWRITE uses existing_text/instruction; the others use brief only).
    brand_voice is injected by the caller from brand_profiles, never client-supplied,
    so it can safely sit alongside the fixed system prompt rather than the untrusted
    user content (THREAT_MODEL.md T56)."""

    brief: str = ""
    existing_text: str | None = None
    instruction: str | None = None
    brand_voice: str | None = None
