import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrandSafetyProfile:
    brand_voice: str | None = None
    brand_tone: str | None = None
    target_audience: str | None = None
    required_facts: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    preferred_vocabulary: list[str] = field(default_factory=list)
    avoid_vocabulary: list[str] = field(default_factory=list)
    compliance_rules: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "BrandSafetyProfile":
        if not data:
            return cls()
        return cls(
            brand_voice=data.get("brand_voice"),
            brand_tone=data.get("brand_tone"),
            target_audience=data.get("target_audience"),
            required_facts=list(data.get("required_facts") or []),
            forbidden_claims=list(data.get("forbidden_claims") or []),
            preferred_vocabulary=list(data.get("preferred_vocabulary") or []),
            avoid_vocabulary=list(data.get("avoid_vocabulary") or []),
            compliance_rules=list(data.get("compliance_rules") or []),
        )


@dataclass
class SafetyScanResult:
    is_safe: bool
    violations: list[str]
    warnings: list[str]
    notes: list[str]


def enrich_system_prompt_with_brand_voice(
    system_prompt: str, brand: BrandSafetyProfile | None
) -> str:
    """Enriches system prompt with brand tone, personas, audience, and strict safety constraints."""
    if not brand:
        return system_prompt

    clauses: list[str] = []

    if brand.brand_tone:
        clauses.append(f"Tone of voice: {brand.brand_tone}.")
    elif brand.brand_voice:
        clauses.append(f"Brand voice: {brand.brand_voice}.")

    if brand.target_audience:
        clauses.append(f"Target audience: {brand.target_audience}.")

    if brand.preferred_vocabulary:
        words = ", ".join(f"'{w}'" for w in brand.preferred_vocabulary[:8])
        clauses.append(f"Preferred terms to naturally weave in when relevant: {words}.")

    if brand.required_facts:
        facts = "; ".join(brand.required_facts[:5])
        clauses.append(f"Accurate brand facts you may highlight: {facts}.")

    # Strict Negative Constraints
    negative_rules: list[str] = []
    if brand.forbidden_claims:
        claims = "; ".join(f"'{c}'" for c in brand.forbidden_claims)
        negative_rules.append(f"NEVER state, imply, or promise: {claims}")

    if brand.avoid_vocabulary:
        avoid = ", ".join(f"'{w}'" for w in brand.avoid_vocabulary[:10])
        negative_rules.append(f"Avoid using these words: {avoid}")

    if brand.compliance_rules:
        compliance = "; ".join(brand.compliance_rules[:5])
        negative_rules.append(f"Mandatory compliance rules: {compliance}")

    if negative_rules:
        clauses.append("STRICT SAFETY RULES: " + " | ".join(negative_rules) + ".")

    if not clauses:
        return system_prompt

    brand_section = " ".join(clauses)
    return f"{system_prompt} Brand Guidelines: {brand_section}"


def check_content_safety(content: str, brand: BrandSafetyProfile | None) -> SafetyScanResult:
    """Performs deterministic post-generation safety scan on generated copy.
    Verifies that forbidden claims and avoid-vocabulary are not present."""
    if not brand or not content:
        return SafetyScanResult(is_safe=True, violations=[], warnings=[], notes=[])

    violations: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []
    lower_content = content.lower()

    # 1. Check forbidden claims (Hard Blocker)
    for claim in brand.forbidden_claims:
        if not claim or not claim.strip():
            continue
        claim_clean = claim.strip().lower()
        if claim_clean in lower_content:
            violations.append(f"Forbidden claim detected: '{claim}'")
        else:
            # Check partial keyword match if claim is multiple words
            words = [w for w in re.split(r"\W+", claim_clean) if len(w) > 4]
            if len(words) >= 2 and all(w in lower_content for w in words):
                violations.append(f"Potential forbidden claim pattern detected: '{claim}'")

    # 2. Check compliance rules
    for rule in brand.compliance_rules:
        if not rule:
            continue
        rule_lower = rule.lower()
        if "disclose" in rule_lower and "#ad" not in lower_content and "sponsored" not in lower_content:
            warnings.append(f"Compliance notice: verify disclosures for rule '{rule}'")

    # 3. Check avoid vocabulary (Soft Warning)
    for word in brand.avoid_vocabulary:
        if not word or not word.strip():
            continue
        clean_word = word.strip().lower()
        pattern = rf"\b{re.escape(clean_word)}\b"
        if re.search(pattern, lower_content):
            warnings.append(f"Discouraged brand vocabulary used: '{word}'")

    # 4. Check required facts presence
    for fact in brand.required_facts:
        if fact and any(w in lower_content for w in fact.lower().split() if len(w) > 5):
            notes.append(f"Incorporated brand fact: '{fact}'")

    is_safe = len(violations) == 0
    return SafetyScanResult(
        is_safe=is_safe,
        violations=violations,
        warnings=warnings,
        notes=notes,
    )
