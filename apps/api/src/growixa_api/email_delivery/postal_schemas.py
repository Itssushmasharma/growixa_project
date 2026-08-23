from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PostalMessageSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | str | None = None
    token: str | None = None
    direction: str | None = None
    message_id: str | None = None
    to: str | None = None
    from_: str | None = Field(default=None, alias="from")
    subject: str | None = None
    tag: str | None = None
    custom_headers: dict[str, Any] = Field(default_factory=dict)
    original_headers: dict[str, Any] = Field(default_factory=dict)


class PostalWebhookPayload(BaseModel):
    """Permissive schema for Postal webhook event payloads."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    event: str
    timestamp: float | int | str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    def extract_message(self) -> PostalMessageSummary:
        msg_dict = self.payload.get("message")
        if isinstance(msg_dict, dict):
            return PostalMessageSummary.model_validate(msg_dict)
        return PostalMessageSummary()

    def extract_occurred_at(self) -> datetime:
        if isinstance(self.timestamp, (int, float)):
            try:
                return datetime.fromtimestamp(self.timestamp, tz=UTC)
            except Exception:
                pass
        return datetime.now(UTC)
