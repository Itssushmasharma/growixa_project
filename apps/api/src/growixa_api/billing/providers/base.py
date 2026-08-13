from dataclasses import dataclass
from typing import Literal, Protocol

TIMEOUT_SECONDS = 30.0


class PaymentGatewayError(Exception):
    """Wraps any failure talking to a payment gateway (network, or a gateway-returned
    error payload) behind one type, mirroring AIProviderError's shape."""


@dataclass
class GatewayPlan:
    gateway_plan_id: str


class PaymentGatewayProvider(Protocol):
    """Adapter interface for a recurring-billing payment gateway, deliberately the same
    shape as AIModelProvider (DEC-GRX-005/026): one concrete implementation per vendor,
    the rest of the billing module only ever talks to this interface. Razorpay
    (razorpay_provider.py) is the one implementation today (DEC-GRX-029) -- adding or
    switching gateways later is a new adapter file, not a rewrite of billing/services.py,
    the quota evaluator, or the webhook handler's event-mapping logic.

    Grown incrementally, task by task, not speculatively: only create_plan() exists yet
    (GRX-BILL-002, needed by the plan-sync script). create_subscription()/
    verify_webhook_signature()/parse_webhook_event() are added when GRX-BILL-003/004
    actually need them.
    """

    async def create_plan(
        self, *, name: str, amount_smallest_unit: int, currency: Literal["USD", "INR"]
    ) -> GatewayPlan: ...
