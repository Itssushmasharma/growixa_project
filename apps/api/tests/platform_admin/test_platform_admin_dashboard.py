"""Platform admin dashboard summary aggregation tests (GRX-SAAS-013 dashboards pass).

Integration-tier: exercises real Postgres and the real create_app() app. Prerequisite
rows (a second plan tier, subscription status changes) are set up directly via the ORM.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.app import create_app
from growixa_api.billing.models import AccountSubscription, SubscriptionPlan
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin
from tests.conftest import DEFAULT_TEST_PASSWORD


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


async def _move_account_to_starter_plan(session: AsyncSession, account_id: uuid.UUID) -> None:
    starter_plan_id = (
        await session.execute(select(SubscriptionPlan.id).where(SubscriptionPlan.slug == "starter"))
    ).scalar_one()
    await session.execute(
        update(AccountSubscription)
        .where(AccountSubscription.account_id == account_id)
        .values(plan_id=starter_plan_id)
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_summary_counts_active_accounts_and_plan_distribution(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    free_account = await account_factory(name="Summary Free Account")
    starter_account = await account_factory(name="Summary Starter Account")

    async with async_session_factory() as session:
        await _move_account_to_starter_plan(session, starter_account)
        await session.commit()

    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_active_accounts"] >= 2

    distribution = {row["plan_slug"]: row["account_count"] for row in body["plan_distribution"]}
    assert "free" in distribution
    assert "starter" in distribution
    assert distribution["starter"] >= 1

    # Both accounts created here are real objects, not asserted by exact id membership --
    # the aggregate counts above are what this endpoint promises (GRX-SAAS-008 /
    # DEC-GRX-021 point 3: an aggregate, never a raw per-record cross-account dump).
    assert free_account is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_summary_requires_authentication() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/platform/dashboard/summary")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_finance_role_is_denied_dashboard_summary(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Same gate as GET /platform/usage (platform.usage.manage) -- platform.finance must
    403, per DEC-GRX-021."""
    admin_id = await platform_admin_factory(role="platform.finance")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        response = await client.get("/platform/dashboard/summary")

    assert response.status_code == 403
