import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from growixa_api.db import Base


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Denormalized from company_id's own account_id (GRX-SAAS-001, defense-in-depth) --
    # queries scope by this directly rather than joining through company_profile.
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("company_profile.id", ondelete="CASCADE"), nullable=False
    )
    brand_voice: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_tone: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    forbidden_claims: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    required_facts: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    preferred_vocabulary: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    avoid_vocabulary: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    compliance_rules: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    # Selected persona chips, e.g. ["Professional", "Confident"] (GRX-COMPANY-003).
    persona_tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    # 0-100 slider values, e.g. {"formality": 70, "energy": 40, "technical_depth": 50,
    # "sales_style": 60}. Free-form JSONB rather than fixed columns since these are UI
    # preference knobs, not queried or validated server-side (GRX-COMPANY-003).
    voice_settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
