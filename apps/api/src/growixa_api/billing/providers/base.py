from dataclasses import dataclass
from typing import Any, Literal, Protocol

TIMEOUT_SECONDS = 30.0


class PaymentGatewayError(Exception):
    """Wraps any failure talking to a payment gateway (network, or a gateway-returned
    error payload) behind one type, mirroring AIProviderError's shape."""


@dataclass
class GatewayPlan:
    gateway_plan_id: str


@dataclass
class GatewaySubscription:
    gateway_subscription_id: str


@dataclass
class GatewayOrder:
    gateway_order_id: str


class PaymentGatewayProvider(Protocol):
    """Adapter interface for a recurring-billing payment gateway, deliberately the same
    shape as AIModelProvider (DEC-GRX-005/026): one concrete implementation per vendor,
    the rest of the billing module only ever talks to this interface. Razorpay
    (razorpay_provider.py) is the one implementation today (DEC-GRX-029) -- adding or
    switching gateways later is a new adapter file, not a rewrite of billing/services.py,
    the quota evaluator, or the webhook handler's event-mapping logic.

    Grown incrementally, task by task, not speculatively: create_plan()/
    verify_webhook_signature() were added in GRX-BILL-002/003; create_subscription()/
    create_order() are added here in GRX-BILL-004, the first task that actually
    initiates a checkout.
    """

    async def create_plan(
        self, *, name: str, amount_smallest_unit: int, currency: Literal["USD", "INR"]
    ) -> GatewayPlan: ...

    def verify_webhook_signature(self, *, payload: bytes, signature: str, secret: str) -> bool:
        """Synchronous, pure -- no I/O. Each gateway signs webhook payloads
        differently (Razorpay: plain HMAC-SHA256 hex digest of the raw body; a future
        Stripe adapter would need its own timestamp-plus-signature scheme), so this
        stays gateway-specific rather than living in the webhook route itself, which
        should never need to know which vendor it's talking to (GRX-BILL-003)."""
        ...

    async def create_subscription(
        self, *, gateway_plan_id: str, notes: dict[str, Any]
    ) -> GatewaySubscription:
        """Creates a not-yet-authorized subscription against an existing Plan
        (GRX-BILL-002's plan-sync CLI is what creates Plans; this never does). The
        returned id is handed to the frontend's checkout widget for the customer to
        actually authorize -- nothing is granted server-side until the
        subscription.activated/charged webhook confirms (GRX-BILL-003)."""
        ...

    async def create_order(
        self, *, amount_smallest_unit: int, currency: Literal["USD", "INR"], notes: dict[str, Any]
    ) -> GatewayOrder:
        """One-time payment (top-up credit packs) -- unlike a subscription, there's no
        pre-created Plan; the amount is set directly per order. `notes` is where the
        webhook handler's `kind=credit_topup` marker and crediting details
        (account_id/credit_type/credits) travel through to `payment.captured`
        (`billing/services.py::_handle_payment_captured`)."""
        ...
