from typing import Any, Literal

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


class SubscribeIn(BaseModel):
    # No "free" (default at registration, no checkout needed) or "enterprise"
    # (contact-sales, platform-admin-activated only, DEC-GRX-030 point 4).
    plan_slug: Literal["starter", "pro"]
    currency: Literal["USD", "INR"]


class SubscribeOut(BaseModel):
    razorpay_subscription_id: str
    # The frontend's Checkout.js widget needs the public key alongside the
    # subscription id -- never the secret, which never leaves the server.
    razorpay_key_id: str


class TopUpIn(BaseModel):
    pack_slug: str
    currency: Literal["USD", "INR"]


class TopUpOut(BaseModel):
    razorpay_order_id: str
    razorpay_key_id: str
    amount_smallest_unit: int
    currency: Literal["USD", "INR"]
