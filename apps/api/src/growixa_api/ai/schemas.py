import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AIProvider = Literal["OPENAI", "AZURE_OPENAI", "ANTHROPIC", "OLLAMA"]


class AIProviderConnectionIn(BaseModel):
    provider: AIProvider
    # Optional -- Ollama typically needs none.
    api_key: str | None = None
    # Required for AZURE_OPENAI/OLLAMA, validated per DEC-GRX-027; not used by
    # OPENAI/ANTHROPIC, which always use their fixed official base URL.
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
