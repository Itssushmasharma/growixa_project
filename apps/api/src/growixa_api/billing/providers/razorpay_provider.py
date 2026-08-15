import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from growixa_api.billing.providers.base import (
    TIMEOUT_SECONDS,
    GatewayOrder,
    GatewayPlan,
    GatewaySubscription,
    PaymentGatewayError,
)

_API_BASE = "https://api.razorpay.com/v1"
_PERIOD = "monthly"
_INTERVAL = 1
# Razorpay requires a total_count (number of billing cycles) on every subscription --
# there's no "renews forever" option. 1200 monthly cycles (100 years) is the standard
# way integrations represent "until cancelled"; a real cancellation still works via the
# subscription.cancelled webhook/GRX-BILL-006's ticker regardless of this number.
_INDEFINITE_TOTAL_COUNT = 1200


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise PaymentGatewayError(
            f"Non-JSON response from Razorpay (HTTP {response.status_code})"
        ) from exc
    if response.is_error:
        message = data.get("error", {}).get("description", data)
        raise PaymentGatewayError(f"Razorpay returned HTTP {response.status_code}: {message}")
    return data


@dataclass
class RazorpayProvider:
    """Raw httpx, no vendor SDK -- matches every other external integration in this
    codebase (Postmark, Supabase Storage, Instagram Graph API, the AI provider
    adapters). Authenticates via HTTP Basic Auth (key_id, key_secret), Razorpay's own
    convention -- see https://razorpay.com/docs/api/authentication/."""

    key_id: str
    key_secret: str

    async def create_plan(
        self, *, name: str, amount_smallest_unit: int, currency: Literal["USD", "INR"]
    ) -> GatewayPlan:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{_API_BASE}/plans",
                    auth=(self.key_id, self.key_secret),
                    json={
                        "period": _PERIOD,
                        "interval": _INTERVAL,
                        "item": {
                            "name": name,
                            "amount": amount_smallest_unit,
                            "currency": currency,
                        },
                    },
                )
        except httpx.HTTPError as exc:
            raise PaymentGatewayError(str(exc)) from exc

        data = _extract_or_raise(response)
        return GatewayPlan(gateway_plan_id=data["id"])

    def verify_webhook_signature(self, *, payload: bytes, signature: str, secret: str) -> bool:
        """Razorpay's own scheme: HMAC-SHA256 hex digest of the raw request body,
        keyed with the webhook secret configured in the dashboard -- sent in the
        `X-Razorpay-Signature` header. See
        https://razorpay.com/docs/webhooks/validate-test/. `hmac.compare_digest`
        avoids a timing side-channel on the comparison itself."""
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def create_subscription(
        self, *, gateway_plan_id: str, notes: dict[str, Any]
    ) -> GatewaySubscription:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{_API_BASE}/subscriptions",
                    auth=(self.key_id, self.key_secret),
                    json={
                        "plan_id": gateway_plan_id,
                        "customer_notify": 1,
                        "total_count": _INDEFINITE_TOTAL_COUNT,
                        "notes": notes,
                    },
                )
        except httpx.HTTPError as exc:
            raise PaymentGatewayError(str(exc)) from exc

        data = _extract_or_raise(response)
        return GatewaySubscription(gateway_subscription_id=data["id"])

    async def create_order(
        self, *, amount_smallest_unit: int, currency: Literal["USD", "INR"], notes: dict[str, Any]
    ) -> GatewayOrder:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{_API_BASE}/orders",
                    auth=(self.key_id, self.key_secret),
                    json={
                        "amount": amount_smallest_unit,
                        "currency": currency,
                        "notes": notes,
                    },
                )
        except httpx.HTTPError as exc:
            raise PaymentGatewayError(str(exc)) from exc

        data = _extract_or_raise(response)
        return GatewayOrder(gateway_order_id=data["id"])
