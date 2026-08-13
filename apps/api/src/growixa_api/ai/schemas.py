import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AIProvider = Literal["OPENAI", "AZURE_OPENAI", "ANTHROPIC", "OLLAMA"]
AICapability = Literal[
    "SUBJECT_LINE", "BODY_COPY", "SOCIAL_CAPTION", "REWRITE", "HASHTAGS", "POSTING_TIME"
]
AILinkedEntityType = Literal["campaign", "social_post"]


class AIProviderConnectionIn(BaseModel):
    provider: AIProvider
    # Optional -- Ollama typically needs none.
    api_key: str | None = None
    # Required for AZURE_OPENAI/OLLAMA, validated per DEC-GRX-027; optional for OPENAI
    # to point at any OpenAI-compatible third-party API instead of the official one
    # (same /chat/completions wire format, different domain), also SSRF-validated when
    # set; not used by ANTHROPIC, which always uses its fixed official base URL.
    base_url: str | None = None
    default_model: str


class AIProviderConnectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: AIProvider
    base_url: str | None
    default_model: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Never the api_key or its encrypted form, in any response.


class PlatformAIProviderConfigIn(BaseModel):
    provider: AIProvider
    api_key: str | None = None
    base_url: str | None = None
    default_model: str


class PlatformAIProviderConfigOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: AIProvider
    base_url: str | None
    default_model: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Never the api_key or its encrypted form, in any response.


class GenerateContentIn(BaseModel):
    brief: str = ""
    # REWRITE only: the text to rewrite, and the change to make (e.g. "shorten",
    # "more casual tone"). Free text, not a fixed enum — the model interprets it
    # directly, per ai/prompts/templates.py's design note.
    existing_text: str | None = None
    instruction: str | None = None
    # Optional provenance — which campaign/social_post this was generated for.
    linked_entity_type: AILinkedEntityType | None = None
    linked_entity_id: uuid.UUID | None = None


class AIGenerationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    capability: AICapability
    output: dict[str, object] | list[object] | None
    provider: AIProvider
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    estimated_cost_usd: float | None
    status: Literal["COMPLETE", "FAILED"]
    error_message: str | None
    linked_entity_type: str | None
    linked_entity_id: uuid.UUID | None
    created_at: datetime
