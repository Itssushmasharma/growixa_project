from dataclasses import dataclass
from typing import Any, Literal

import httpx

from growixa_api.billing.providers.base import (
    TIMEOUT_SECONDS,
    GatewayPlan,
    PaymentGatewayError,
)

_API_BASE = "https://api.razorpay.com/v1"
_PERIOD = "monthly"
_INTERVAL = 1


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
