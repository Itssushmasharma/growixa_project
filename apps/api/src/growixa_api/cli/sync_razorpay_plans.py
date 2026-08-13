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

    async with async_session_factory() as session:
        result = await session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.price_usd.is_not(None))
        )
        plans = result.scalars().all()

        if not plans:
            print("No paid plans found -- nothing to sync.")
            return 0

        for plan in plans:
            if plan.razorpay_plan_id_usd is None and plan.price_usd is not None:
                gateway_plan = await gateway.create_plan(
                    name=f"Growixa {plan.name} (USD)",
                    amount_smallest_unit=int(plan.price_usd * 100),
                    currency="USD",
                )
                plan.razorpay_plan_id_usd = gateway_plan.gateway_plan_id
                print(f"Created Razorpay Plan {gateway_plan.gateway_plan_id} for {plan.slug} (USD)")

            if plan.razorpay_plan_id_inr is None and plan.price_inr is not None:
                gateway_plan = await gateway.create_plan(
                    name=f"Growixa {plan.name} (INR)",
                    amount_smallest_unit=int(plan.price_inr * 100),
                    currency="INR",
                )
                plan.razorpay_plan_id_inr = gateway_plan.gateway_plan_id
                print(f"Created Razorpay Plan {gateway_plan.gateway_plan_id} for {plan.slug} (INR)")

        await session.commit()

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
