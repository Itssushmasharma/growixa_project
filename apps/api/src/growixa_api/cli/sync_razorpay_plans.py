"""One-time (and safely re-runnable) Razorpay Plan sync command.

Usage:
    docker compose exec api python -m growixa_api.cli.sync_razorpay_plans

Creates a Razorpay Plan object (via the Razorpay API, not the dashboard) for every
paid subscription_plans row/currency combination that doesn't have one yet, and
stores the returned plan_id back onto that row. Free and Enterprise never get a
Razorpay Plan (no fixed self-serve price for either, DEC-GRX-030) -- only
starter/pro x USD/INR, four Plans total.

Idempotent: a row/currency combination that already has a razorpay_plan_id_* value is
skipped, so re-running after adding a new plan tier only creates what's missing. Reads
RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET from the environment (config.Settings) -- run this
against Test Mode credentials first; Live Mode Plans are a separate, deliberate step.

If you ever change a plan's price, don't edit the existing Razorpay Plan (Razorpay
treats Plans as immutable so existing subscribers' price never silently changes) --
clear that plan's razorpay_plan_id_usd/inr and re-run this command to mint a new one;
GRX-SAAS-006's admin "edit plan price" action will eventually do this step
automatically.
"""

import asyncio
import sys

from sqlalchemy import select

from growixa_api.billing.models import SubscriptionPlan
from growixa_api.billing.providers.base import PaymentGatewayError
from growixa_api.billing.providers.razorpay_provider import RazorpayProvider
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory


async def main() -> int:
    settings = get_settings()
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        print(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must both be set.",
            file=sys.stderr,
        )
        return 1

    gateway = RazorpayProvider(
        key_id=settings.razorpay_key_id, key_secret=settings.razorpay_key_secret
    )
    had_failure = False

    async with async_session_factory() as session:
        # Strictly positive price -- not `IS NOT NULL`. Free is priced at a real `0`
        # (not NULL), and Razorpay rejects a zero-amount Plan outright ("amount must be
        # at least $0.1"); Enterprise's NULL price is already excluded by `> 0`, no
        # separate NULL check needed. Found live: the original `IS NOT NULL` filter
        # tried to create a $0 Plan for Free and Razorpay correctly rejected it.
        result = await session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.price_usd > 0)
        )
        plans = result.scalars().all()

        if not plans:
            print("No paid plans found -- nothing to sync.")
            return 0

        # Each currency is created and committed independently -- one currency being
        # rejected by the gateway (e.g. international/USD payments not yet approved on
        # the account) must not lose progress on the ones that do succeed, and must not
        # abort the whole run. Found live: the original single-commit-at-the-end
        # design meant a USD failure silently discarded already-created INR plans too.
        for plan in plans:
            if plan.razorpay_plan_id_usd is None and plan.price_usd and plan.price_usd > 0:
                try:
                    gateway_plan = await gateway.create_plan(
                        name=f"Growixa {plan.name} (USD)",
                        amount_smallest_unit=int(plan.price_usd * 100),
                        currency="USD",
                    )
                except PaymentGatewayError as exc:
                    print(f"FAILED: {plan.slug} (USD): {exc}", file=sys.stderr)
                    had_failure = True
                else:
                    plan.razorpay_plan_id_usd = gateway_plan.gateway_plan_id
                    await session.commit()
                    print(
                        f"Created Razorpay Plan {gateway_plan.gateway_plan_id} for "
                        f"{plan.slug} (USD)"
                    )

            if plan.razorpay_plan_id_inr is None and plan.price_inr and plan.price_inr > 0:
                try:
                    gateway_plan = await gateway.create_plan(
                        name=f"Growixa {plan.name} (INR)",
                        amount_smallest_unit=int(plan.price_inr * 100),
                        currency="INR",
                    )
                except PaymentGatewayError as exc:
                    print(f"FAILED: {plan.slug} (INR): {exc}", file=sys.stderr)
                    had_failure = True
                else:
                    plan.razorpay_plan_id_inr = gateway_plan.gateway_plan_id
                    await session.commit()
                    print(
                        f"Created Razorpay Plan {gateway_plan.gateway_plan_id} for "
                        f"{plan.slug} (INR)"
                    )

    if had_failure:
        print(
            "Done, with failures -- re-run this command once the underlying gateway "
            "issue (e.g. currency support) is resolved; already-created plans were not "
            "re-created (idempotent).",
            file=sys.stderr,
        )
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
