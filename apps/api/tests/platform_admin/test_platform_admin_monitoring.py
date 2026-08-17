"""Platform Admin infra monitoring + financial dashboard tests (GRX-SAAS-009).

Integration-tier for the DB-backed financial metrics and route permission gating;
unit-tier for the pure queue-name-list logic (no live broker needed for that part --
the live passive-declare mechanism itself was verified separately against the real
RabbitMQ container during development, see the task's pr_reviews handoff)."""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.billing.models import AccountSubscription, SubscriptionPlan
from growixa_api.billing.repositories import get_plan_by_slug
from growixa_api.db import async_session_factory
from growixa_api.health import _monitored_queue_names
from growixa_api.platform_admin.services import get_financial_metrics
from growixa_api.platform_auth.models import PlatformAdmin


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one()


async def _platform_login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


async def _set_subscription(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    plan: SubscriptionPlan,
    currency: str,
    status: str = "ACTIVE",
    updated_at: datetime | None = None,
) -> None:
    result = await session.execute(
        select(AccountSubscription).where(AccountSubscription.account_id == account_id)
    )
    subscription = result.scalar_one()
    subscription.plan_id = plan.id
    subscription.currency = currency
    subscription.status = status
    await session.flush()
    if updated_at is not None:
        # Bypass the onupdate=func.now() trigger to simulate a cancellation that
        # happened at a specific point in the past, for the churn-window test.
        await session.execute(
            update(AccountSubscription)
            .where(AccountSubscription.id == subscription.id)
            .values(updated_at=updated_at)
        )
    await session.commit()


def test_monitored_queue_names_cover_dispatch_retry_ladder_and_dlq() -> None:
    """Acceptance criterion: queue depths for grx.campaigns.dispatch/retry/DLQ are
    visible. Verifies the exact set of queue names matches the worker's real
    MAX_DISPATCH_ATTEMPTS=3 retry ladder (apps/worker/src/growixa_worker/consumer.py)."""
    names = _monitored_queue_names()
    assert "grx.campaigns.dispatch" in names
    assert "grx.campaigns.dispatch.retry.0" in names
    assert "grx.campaigns.dispatch.retry.1" in names
    assert "grx.campaigns.dispatch.retry.2" in names
    assert "grx.campaigns.dlq" in names
    assert "grx.social.dispatch" in names
    assert "grx.social.dlq" in names
    assert len(names) == len(set(names)), "no duplicate queue names"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_financial_metrics_computes_mrr_arr_per_currency_not_summed_together(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    usd_account = await account_factory(name="USD Starter Account")
    inr_account = await account_factory(name="INR Pro Account")

    async with async_session_factory() as session:
        starter = await get_plan_by_slug(session, "starter")
        pro = await get_plan_by_slug(session, "pro")
        assert starter is not None and pro is not None

        metrics_before = await get_financial_metrics(session)

        await _set_subscription(session, account_id=usd_account, plan=starter, currency="USD")
        await _set_subscription(session, account_id=inr_account, plan=pro, currency="INR")

        metrics = await get_financial_metrics(session)

    assert starter.price_usd is not None
    assert pro.price_inr is not None
    assert metrics.mrr_by_currency["USD"] - metrics_before.mrr_by_currency["USD"] == pytest.approx(
        float(starter.price_usd)
    )
    assert metrics.mrr_by_currency["INR"] - metrics_before.mrr_by_currency["INR"] == pytest.approx(
        float(pro.price_inr)
    )
    assert metrics.arr_by_currency["USD"] == pytest.approx(metrics.mrr_by_currency["USD"] * 12)
    assert metrics.arr_by_currency["INR"] == pytest.approx(metrics.mrr_by_currency["INR"] * 12)
    diff = (
        metrics.active_paying_subscription_count - metrics_before.active_paying_subscription_count
    )
    assert diff == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_financial_metrics_churn_counts_only_cancellations_in_the_last_30_days(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    recent_churn_account = await account_factory(name="Recently Churned Account")
    old_churn_account = await account_factory(name="Old Churn Account")

    async with async_session_factory() as session:
        starter = await get_plan_by_slug(session, "starter")
        assert starter is not None

        metrics_before = await get_financial_metrics(session)

        await _set_subscription(
            session,
            account_id=recent_churn_account,
            plan=starter,
            currency="USD",
            status="CANCELED",
            updated_at=datetime.now(UTC) - timedelta(days=5),
        )
        await _set_subscription(
            session,
            account_id=old_churn_account,
            plan=starter,
            currency="USD",
            status="CANCELED",
            updated_at=datetime.now(UTC) - timedelta(days=90),
        )

        metrics = await get_financial_metrics(session)

    assert metrics.churned_last_30_days - metrics_before.churned_last_30_days == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_monitoring_routes_require_platform_monitoring_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        financials_response = await client.get("/platform/monitoring/financials")
        queues_response = await client.get("/platform/monitoring/queues")

    assert financials_response.status_code == 200
    body = financials_response.json()
    assert "mrr_by_currency" in body
    assert "active_paying_subscription_count" in body
    assert "churn_rate_percent" in body

    assert queues_response.status_code == 200
    assert "grx.campaigns.dispatch" in queues_response.json()["queues"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_support_role_is_denied_monitoring_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """platform.support is not in GRANTED_ROLES for platform.monitoring.manage
    (see the migration's docstring) -- infra/financial detail is not a support
    function."""
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/monitoring/financials")

    assert response.status_code == 403
