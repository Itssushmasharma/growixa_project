"""Atomic quota evaluator tests (GRX-BILL-005, GRX-BILL-008).

Integration-tier: exercises real Postgres. The AI capability provider call itself is
monkeypatched at the get_effective_ai_provider boundary for the two route-level tests,
same convention as test_ai_generate.py; the race-condition and credit-fallback tests
call check_and_consume_quota directly against real Postgres since that's the unit
whose exact locking/atomicity behavior is under test.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update

from growixa_api.ai import services as ai_services
from growixa_api.ai.models import AIGeneration, AIProviderConnection, PlatformAIProviderConfig
from growixa_api.ai.providers.base import AIGenerationResult
from growixa_api.ai.providers.factory import ResolvedAIProvider
from growixa_api.app import create_app
from growixa_api.billing.models import AccountCreditBalance, AccountSubscription, SubscriptionPlan
from growixa_api.billing.services import QuotaExceededError, check_and_consume_quota
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.usage.models import UsageRecord


class _FakeProvider:
    async def generate(
        self, *, system_prompt: str, user_prompt: str, model: str, max_tokens: int
    ) -> AIGenerationResult:
        return AIGenerationResult(text="generated text", prompt_tokens=10, completion_tokens=5)


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


def _patch_provider(monkeypatch: pytest.MonkeyPatch, *, source: str) -> None:
    async def _fake_get_effective_ai_provider(
        session: object, account_id: uuid.UUID
    ) -> ResolvedAIProvider:
        return ResolvedAIProvider(
            provider=_FakeProvider(),
            provider_name="OPENAI",
            model="gpt-4o-mini",
            source=source,  # type: ignore[arg-type]
        )

    monkeypatch.setattr(ai_services, "get_effective_ai_provider", _fake_get_effective_ai_provider)


async def _free_plan_ai_limit() -> int:
    async with async_session_factory() as session:
        limit = (
            await session.execute(
                select(SubscriptionPlan.max_monthly_ai_runs).where(SubscriptionPlan.slug == "free")
            )
        ).scalar_one()
        assert limit is not None, "Free plan must have a real (non-NULL) monthly AI run cap"
        return limit


async def _set_period_ai_used(account_id: uuid.UUID, used: int) -> None:
    async with async_session_factory() as session:
        await session.execute(
            update(AccountSubscription)
            .where(AccountSubscription.account_id == account_id)
            .values(period_ai_used=used)
        )
        await session.commit()


async def _cleanup(account_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AIGeneration).where(AIGeneration.account_id == account_id))
        await session.execute(
            delete(UsageRecord).where(UsageRecord.operation_type == "ai_generation")
        )
        await session.execute(
            delete(AIProviderConnection).where(AIProviderConnection.account_id == account_id)
        )
        await session.execute(delete(PlatformAIProviderConfig))
        await session.execute(
            delete(AccountCreditBalance).where(AccountCreditBalance.account_id == account_id)
        )
        await session.execute(
            update(AccountSubscription)
            .where(AccountSubscription.account_id == account_id)
            .values(period_ai_used=0)
        )
        await session.commit()


@pytest.fixture
async def quota_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_ai_generation_beyond_plan_allowance_is_blocked_with_402(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    quota_account_id: uuid.UUID,
) -> None:
    """Negative half of the sprint's negative+positive pair: a platform-provided
    generation with no top-up credit balance to fall back on is blocked."""
    _patch_provider(monkeypatch, source="PLATFORM_DEFAULT")
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=quota_account_id
    )
    limit = await _free_plan_ai_limit()
    await _set_period_ai_used(quota_account_id, limit)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "a running shoe sale"}
            )

        assert response.status_code == 402
    finally:
        await _cleanup(quota_account_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_ai_generation_covered_by_credit_balance_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    quota_account_id: uuid.UUID,
) -> None:
    """Positive half of the pair: the same over-quota account succeeds once a
    non-expiring AI_RUNS top-up credit balance is available to cover the overage."""
    _patch_provider(monkeypatch, source="PLATFORM_DEFAULT")
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=quota_account_id
    )
    limit = await _free_plan_ai_limit()
    await _set_period_ai_used(quota_account_id, limit)
    async with async_session_factory() as session:
        session.add(
            AccountCreditBalance(
                account_id=quota_account_id, credit_type="AI_RUNS", remaining_credits=5
            )
        )
        await session.commit()
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "a running shoe sale"}
            )

        assert response.status_code == 200

        async with async_session_factory() as session:
            balance = (
                await session.execute(
                    select(AccountCreditBalance).where(
                        AccountCreditBalance.account_id == quota_account_id
                    )
                )
            ).scalar_one()
        assert balance.remaining_credits == 4
    finally:
        await _cleanup(quota_account_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_byo_ai_generation_is_never_metered_even_when_plan_allowance_is_exhausted(
    monkeypatch: pytest.MonkeyPatch,
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    quota_account_id: uuid.UUID,
) -> None:
    """BILLING_SYSTEM_ARCHITECTURE.md §4.1: an account's own bring-your-own AI key
    generation is never blocked by this quota and never increments period_ai_used --
    it costs Growixa nothing."""
    _patch_provider(monkeypatch, source="ACCOUNT_BYO")
    manager_id = await user_factory(
        full_name="Marketing Manager", role_name="Marketing Manager", account_id=quota_account_id
    )
    limit = await _free_plan_ai_limit()
    await _set_period_ai_used(quota_account_id, limit)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.post(
                "/ai/generate/SUBJECT_LINE", json={"brief": "a running shoe sale"}
            )

        assert response.status_code == 200

        async with async_session_factory() as session:
            subscription = (
                await session.execute(
                    select(AccountSubscription).where(
                        AccountSubscription.account_id == quota_account_id
                    )
                )
            ).scalar_one()
        assert subscription.period_ai_used == limit
    finally:
        await _cleanup(quota_account_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_two_concurrent_metered_requests_past_the_limit_only_one_succeeds(
    quota_account_id: uuid.UUID,
) -> None:
    """Race-condition test against the atomic evaluator's SELECT ... FOR UPDATE lock
    (GRX-BILL-005): with exactly one unit of headroom left, two concurrent qty=1
    requests must not both succeed."""
    limit = await _free_plan_ai_limit()
    await _set_period_ai_used(quota_account_id, limit - 1)

    async def _attempt() -> bool:
        async with async_session_factory() as session:
            try:
                await check_and_consume_quota(
                    session, account_id=quota_account_id, operation="ai_run", qty=1
                )
                return True
            except QuotaExceededError:
                return False

    try:
        results = await asyncio.gather(_attempt(), _attempt())
        assert sorted(results) == [False, True]

        async with async_session_factory() as session:
            subscription = (
                await session.execute(
                    select(AccountSubscription).where(
                        AccountSubscription.account_id == quota_account_id
                    )
                )
            ).scalar_one()
        assert subscription.period_ai_used == limit
    finally:
        await _cleanup(quota_account_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_quota_exceeded_when_neither_plan_allowance_nor_credit_balance_cover_it(
    quota_account_id: uuid.UUID,
) -> None:
    limit = await _free_plan_ai_limit()
    await _set_period_ai_used(quota_account_id, limit)
    try:
        async with async_session_factory() as session:
            with pytest.raises(QuotaExceededError):
                await check_and_consume_quota(
                    session, account_id=quota_account_id, operation="ai_run", qty=1
                )
    finally:
        await _cleanup(quota_account_id)
