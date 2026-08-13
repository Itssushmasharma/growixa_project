from typing import Any

from pydantic import BaseModel, ConfigDict


class RazorpayWebhookPayload(BaseModel):
    """Deliberately permissive, same convention as PostmarkWebhookPayload
    (email_delivery/schemas.py) -- Razorpay's `payload` shape varies significantly by
    `event` type (subscription.* events nest a `subscription` entity, payment.captured
    nests a `payment` entity). Only `event` itself is required; everything else is
    read defensively in services.py rather than strictly typed here."""

    model_config = ConfigDict(extra="allow")

    event: str
    payload: dict[str, Any] = {}
