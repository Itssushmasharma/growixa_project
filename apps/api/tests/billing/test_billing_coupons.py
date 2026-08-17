"""Coupon/discount engine tests (GRX-SAAS-012, GRX-BILL-008).

Integration-tier: exercises real Postgres and the real create_app() app. The Razorpay
Order call in the percentage-discount test is monkeypatched at billing.api's private
_gateway() boundary (no live Razorpay account reachable from the test environment,
same convention as every other external-provider test in this suite) -- everything
else (discount math, coupon validation, redemption bookkeeping) runs for real.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.billing import api as billing_api
from growixa_api.billing.models import (
    AccountCreditBalance,
    CouponCode,
    CouponRedemption,
    CreditPack,
)
from growixa_api.billing.providers.base import GatewayOrder
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.users.models import User


class _FakeGateway:
    def __init__(self) -> None:
        self.last_amount_smallest_unit: int | None = None

    async def create_order(
        self, *, amount_smallest_unit: int, currency: str, notes: dict[str, object]
    ) -> GatewayOrder:
        self.last_amount_smallest_unit = amount_smallest_unit
        return GatewayOrder(gateway_order_id="order_fake_123")


async def _create_coupon(
    *,
    platform_admin_id: uuid.UUID,
    code: str,
    discount_type: str,
    discount_value: float,
    credit_type: str | None = None,
    max_redemptions: int | None = None,
    expires_at: datetime | None = None,
    applicable_plan_slugs: list[str] | None = None,
    is_active: bool = True,
) -> uuid.UUID:
    async with async_session_factory() as session:
        coupon = CouponCode(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            credit_type=credit_type,
            max_redemptions=max_redemptions,
            expires_at=expires_at,
            applicable_plan_slugs=applicable_plan_slugs,
            is_active=is_active,
            created_by_platform_admin_id=platform_admin_id,
        )
        session.add(coupon)
        await session.commit()
        return coupon.id


async def _create_pack(*, slug: str) -> uuid.UUID:
    async with async_session_factory() as session:
        pack = CreditPack(
            slug=slug, name="Test Pack", credit_type="AI_RUNS", credits=250, price_inr=400.0
        )
        session.add(pack)
        await session.commit()
        return pack.id


async def _cleanup(
    *,
    coupon_ids: list[uuid.UUID],
    pack_ids: list[uuid.UUID],
    account_ids: list[uuid.UUID],
    user_ids: list[uuid.UUID] | None = None,
) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(CouponRedemption).where(CouponRedemption.coupon_code_id.in_(coupon_ids))
        )
        await session.execute(delete(CouponCode).where(CouponCode.id.in_(coupon_ids)))
        await session.execute(delete(CreditPack).where(CreditPack.id.in_(pack_ids)))
        for account_id in account_ids:
            await session.execute(
                delete(AccountCreditBalance).where(AccountCreditBalance.account_id == account_id)
            )
        # /auth/login writes a security-event audit_logs row keyed on actor_user_id,
        # which has no ON DELETE CASCADE (GRX-AUDIT-001) -- must be cleared before
        # user_factory's own teardown deletes the user, or that teardown 500s.
        for user_id in user_ids or []:
            await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
        await session.commit()


async def _login_customer(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


async def _login_platform_admin(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


async def _get_user_email(user_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        return (await session.execute(select(User.email).where(User.id == user_id))).scalar_one()


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        return (
            await session.execute(select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id))
        ).scalar_one()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_credit_grant_coupon_redemption_credits_the_account(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="FREEAI25",
        discount_type="CREDIT_GRANT",
        discount_value=25,
        credit_type="AI_RUNS",
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            response = await client.post("/billing/redeem-coupon", json={"code": "FREEAI25"})

        assert response.status_code == 201
        assert response.json()["remaining_credits"] == 25
    finally:
        await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[], user_ids=[user_id])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_one_redemption_per_account_is_enforced(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="ONCEONLY",
        discount_type="CREDIT_GRANT",
        discount_value=10,
        credit_type="AI_RUNS",
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            first = await client.post("/billing/redeem-coupon", json={"code": "ONCEONLY"})
            second = await client.post("/billing/redeem-coupon", json={"code": "ONCEONLY"})

        assert first.status_code == 201
        assert second.status_code == 409
    finally:
        await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[], user_ids=[user_id])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_max_redemptions_limit_is_enforced_across_accounts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    user_a = await user_factory(full_name="Customer A", role_name="Super Admin")
    user_b = await user_factory(full_name="Customer B", role_name="Super Admin")
    email_a = await _get_user_email(user_a)
    email_b = await _get_user_email(user_b)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="LIMITED1",
        discount_type="CREDIT_GRANT",
        discount_value=10,
        credit_type="AI_RUNS",
        max_redemptions=1,
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client_a:
            await _login_customer(client_a, email_a)
            first = await client_a.post("/billing/redeem-coupon", json={"code": "LIMITED1"})
        async with AsyncClient(transport=transport, base_url="http://test") as client_b:
            await _login_customer(client_b, email_b)
            second = await client_b.post("/billing/redeem-coupon", json={"code": "LIMITED1"})

        assert first.status_code == 201
        assert second.status_code == 400
    finally:
        await _cleanup(
            coupon_ids=[coupon_id], pack_ids=[], account_ids=[], user_ids=[user_a, user_b]
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_expired_coupon_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="EXPIRED1",
        discount_type="CREDIT_GRANT",
        discount_value=10,
        credit_type="AI_RUNS",
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            response = await client.post("/billing/redeem-coupon", json={"code": "EXPIRED1"})

        assert response.status_code == 400
    finally:
        await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[], user_ids=[user_id])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_inactive_coupon_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="OFFNOW1",
        discount_type="CREDIT_GRANT",
        discount_value=10,
        credit_type="AI_RUNS",
        is_active=False,
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            response = await client.post("/billing/redeem-coupon", json={"code": "OFFNOW1"})

        assert response.status_code == 400
    finally:
        await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[], user_ids=[user_id])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_coupon_not_eligible_for_accounts_current_plan_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """The account_factory/user_factory default plan is Free -- a coupon restricted to
    ["pro"] must be rejected for it."""
    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="PROONLY1",
        discount_type="CREDIT_GRANT",
        discount_value=10,
        credit_type="AI_RUNS",
        applicable_plan_slugs=["pro"],
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            response = await client.post("/billing/redeem-coupon", json={"code": "PROONLY1"})

        assert response.status_code == 400
    finally:
        await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[], user_ids=[user_id])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_percentage_coupon_discounts_the_topup_order_amount(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    fake_gateway = _FakeGateway()
    monkeypatch.setattr(billing_api, "_gateway", lambda: fake_gateway)

    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="SAVE20TEST",
        discount_type="PERCENTAGE",
        discount_value=20,
    )
    pack_id = await _create_pack(slug="topup_test_pack")
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            response = await client.post(
                "/billing/topup",
                json={
                    "pack_slug": "topup_test_pack",
                    "currency": "INR",
                    "coupon_code": "SAVE20TEST",
                },
            )

        assert response.status_code == 201
        # ₹400 base -> 40000 paise -> 20% off -> 32000 paise
        assert response.json()["amount_smallest_unit"] == 32000
        assert fake_gateway.last_amount_smallest_unit == 32000
    finally:
        await _cleanup(
            coupon_ids=[coupon_id], pack_ids=[pack_id], account_ids=[], user_ids=[user_id]
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_credit_grant_coupon_is_rejected_at_topup_wrong_endpoint(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    user_id = await user_factory(full_name="Customer", role_name="Super Admin")
    email = await _get_user_email(user_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="WRONGKIND1",
        discount_type="CREDIT_GRANT",
        discount_value=10,
        credit_type="AI_RUNS",
    )
    pack_id = await _create_pack(slug="wrongkind_pack")
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_customer(client, email)
            response = await client.post(
                "/billing/topup",
                json={
                    "pack_slug": "wrongkind_pack",
                    "currency": "INR",
                    "coupon_code": "WRONGKIND1",
                },
            )

        assert response.status_code == 400
    finally:
        await _cleanup(
            coupon_ids=[coupon_id], pack_ids=[pack_id], account_ids=[], user_ids=[user_id]
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_owner_can_create_and_toggle_a_coupon(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)
    coupon_id: uuid.UUID | None = None
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_platform_admin(client, admin_email)
            create_response = await client.post(
                "/platform/coupons",
                json={"code": "OWNERTEST1", "discount_type": "PERCENTAGE", "discount_value": 15},
            )
            assert create_response.status_code == 201
            coupon_id = uuid.UUID(create_response.json()["id"])

            toggle_response = await client.patch(
                f"/platform/coupons/{coupon_id}", json={"is_active": False}
            )
            assert toggle_response.status_code == 200
            assert toggle_response.json()["is_active"] is False
    finally:
        if coupon_id is not None:
            await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_billing_platform_admin_gets_403_on_coupon_routes(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """platform.support holds no platform.billing.manage (RBAC.md's Sprint 5 Phase B
    role table) -- matches this sprint's own acceptance criterion for the other three
    platform.billing.manage-gated actions."""
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login_platform_admin(client, admin_email)
        list_response = await client.get("/platform/coupons")
        create_response = await client.post(
            "/platform/coupons",
            json={"code": "SHOULDFAIL1", "discount_type": "PERCENTAGE", "discount_value": 15},
        )

    assert list_response.status_code == 403
    assert create_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_credit_grant_coupon_missing_credit_type_is_rejected(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login_platform_admin(client, admin_email)
        response = await client.post(
            "/platform/coupons",
            json={"code": "NOCREDITTYPE1", "discount_type": "CREDIT_GRANT", "discount_value": 10},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_coupon_code_is_rejected(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)
    coupon_id = await _create_coupon(
        platform_admin_id=admin_id,
        code="DUPETEST1",
        discount_type="PERCENTAGE",
        discount_value=10,
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _login_platform_admin(client, admin_email)
            response = await client.post(
                "/platform/coupons",
                json={"code": "DUPETEST1", "discount_type": "PERCENTAGE", "discount_value": 5},
            )

        assert response.status_code == 409
    finally:
        await _cleanup(coupon_ids=[coupon_id], pack_ids=[], account_ids=[])
