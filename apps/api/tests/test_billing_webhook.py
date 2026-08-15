"""Razorpay webhook receiver tests (GRX-BILL-003, GRX-BILL-008).

Integration-tier: exercises real Postgres and the real create_app() app. No live
Razorpay account is called -- the webhook signature is computed with the same HMAC
scheme RazorpayProvider.verify_webhook_signature uses, keyed with the test
environment's razorpay_webhook_secret (empty string by default, see .env.test), so a
"real" signature is trivially reproducible without any network call.
"""

import hashlib
import hmac
import json
import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.billing.models import AccountCreditBalance, AccountCreditPurchase, CreditPack
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory


def _sign(payload: bytes) -> str:
    secret = get_settings().razorpay_webhook_secret
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


async def _create_pack(*, slug: str = "ai_runs_test") -> uuid.UUID:
    async with async_session_factory() as session:
        pack = CreditPack(
            slug=slug, name="Test AI Runs", credit_type="AI_RUNS", credits=100, price_inr=100.0
        )
        session.add(pack)
        await session.commit()
        return pack.id


async def _cleanup(account_id: uuid.UUID, pack_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(AccountCreditPurchase).where(AccountCreditPurchase.account_id == account_id)
        )
        await session.execute(
            delete(AccountCreditBalance).where(AccountCreditBalance.account_id == account_id)
        )
        await session.execute(delete(CreditPack).where(CreditPack.id == pack_id))
        await session.commit()


def _topup_payload(*, account_id: uuid.UUID, razorpay_payment_id: str) -> dict[str, object]:
    return {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": razorpay_payment_id,
                    "notes": {
                        "kind": "credit_topup",
                        "account_id": str(account_id),
                        "credit_type": "AI_RUNS",
                        "credits": "100",
                    },
                }
            }
        },
    }


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_rejects_wrong_signature(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    pack_id = await _create_pack()
    try:
        body = _topup_payload(account_id=account_id, razorpay_payment_id="pay_wrong_sig")
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/billing/razorpay",
                content=json.dumps(body),
                headers={
                    "content-type": "application/json",
                    "X-Razorpay-Signature": "not-the-real-signature",
                },
            )

        assert response.status_code == 401

        async with async_session_factory() as session:
            balance = (
                await session.execute(
                    select(AccountCreditBalance).where(
                        AccountCreditBalance.account_id == account_id
                    )
                )
            ).scalar_one_or_none()
        assert balance is None
    finally:
        await _cleanup(account_id, pack_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_webhook_credits_a_topup_on_valid_signature(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    pack_id = await _create_pack()
    try:
        body = _topup_payload(account_id=account_id, razorpay_payment_id="pay_valid_once")
        raw = json.dumps(body).encode()
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/billing/razorpay",
                content=raw,
                headers={
                    "content-type": "application/json",
                    "X-Razorpay-Signature": _sign(raw),
                },
            )

        assert response.status_code == 200

        async with async_session_factory() as session:
            balance = (
                await session.execute(
                    select(AccountCreditBalance).where(
                        AccountCreditBalance.account_id == account_id
                    )
                )
            ).scalar_one()
        assert balance.remaining_credits == 100
    finally:
        await _cleanup(account_id, pack_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_replayed_payment_captured_event_does_not_double_credit(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """THREAT_MODEL.md T61 -- a webhook redelivery of the same payment.captured event
    (same razorpay_payment_id) must be a no-op the second time, not a second grant."""
    account_id = await account_factory()
    pack_id = await _create_pack()
    try:
        body = _topup_payload(account_id=account_id, razorpay_payment_id="pay_replayed_once")
        raw = json.dumps(body).encode()
        signature = _sign(raw)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(
                "/billing/razorpay",
                content=raw,
                headers={"content-type": "application/json", "X-Razorpay-Signature": signature},
            )
            second = await client.post(
                "/billing/razorpay",
                content=raw,
                headers={"content-type": "application/json", "X-Razorpay-Signature": signature},
            )

        assert first.status_code == 200
        assert second.status_code == 200

        async with async_session_factory() as session:
            balance = (
                await session.execute(
                    select(AccountCreditBalance).where(
                        AccountCreditBalance.account_id == account_id
                    )
                )
            ).scalar_one()
            purchases = (
                (
                    await session.execute(
                        select(AccountCreditPurchase).where(
                            AccountCreditPurchase.account_id == account_id
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert balance.remaining_credits == 100
        assert len(purchases) == 1
    finally:
        await _cleanup(account_id, pack_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unrecognized_event_type_is_acknowledged_and_ignored(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """A webhook endpoint's job is to acknowledge receipt so Razorpay doesn't retry
    indefinitely, not to validate Razorpay's own event catalog."""
    body = {"event": "some.future.event.type", "payload": {}}
    raw = json.dumps(body).encode()
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/billing/razorpay",
            content=raw,
            headers={"content-type": "application/json", "X-Razorpay-Signature": _sign(raw)},
        )

    assert response.status_code == 200
