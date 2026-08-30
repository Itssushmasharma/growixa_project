"""Audit log viewing endpoint tests (GRX-AUDIT-002).

Integration-tier: exercises real Postgres and the real create_app() app, using the shared
user_factory fixture (conftest.py) plus directly-inserted audit_logs rows.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import record_event
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.pagination import DEFAULT_LIMIT, MAX_LIMIT


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_list_audit_logs(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(full_name="Audit Admin", role_name="Admin", account_id=account_id)
    entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=admin_id,
            action="contact.created",
            entity_type="contact",
            entity_id=entity_id,
            metadata={"email": "someone@example.com"},
        )
        await session.commit()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.get("/audit")

    assert response.status_code == 200
    events = [row for row in response.json() if row["entity_id"] == str(entity_id)]
    assert len(events) == 1
    assert events[0]["action"] == "contact.created"
    assert events[0]["actor_user_id"] == str(admin_id)
    assert events[0]["event_metadata"] == {"email": "someone@example.com"}

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == admin_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_filter_audit_logs_by_entity_type(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(full_name="Audit Admin", role_name="Admin", account_id=account_id)
    contact_entity_id = uuid.uuid4()
    user_entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=admin_id,
            action="contact.created",
            entity_type="contact",
            entity_id=contact_entity_id,
            metadata={},
        )
        await record_event(
            session,
            account_id=account_id,
            actor_user_id=admin_id,
            action="role.changed",
            entity_type="user",
            entity_id=user_entity_id,
            metadata={},
        )
        await session.commit()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.get("/audit", params={"entity_type": "contact"})

    assert response.status_code == 200
    entity_ids = {row["entity_id"] for row in response.json()}
    assert str(contact_entity_id) in entity_ids
    assert str(user_entity_id) not in entity_ids

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == admin_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_without_audit_view_gets_403(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Plain Analyst", role_name="Analyst")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        response = await client.get("/audit")

    assert response.status_code == 403


async def _seed_audit_logs(
    account_id: uuid.UUID, actor_id: uuid.UUID, count: int
) -> list[uuid.UUID]:
    """Inserts `count` audit_logs rows directly with a distinct, descending `created_at`
    (one second apart) -- `record_event`'s server-side `now()` is transaction-stable, so
    looping calls to it within one commit would give every row the same timestamp and make
    `ORDER BY created_at DESC` pagination non-deterministic. Returns the `entity_id` of
    each inserted row, since `AuditLogOut` doesn't expose `account_id` for isolation
    assertions to key off directly."""
    base = datetime.now(UTC)
    entity_ids = [uuid.uuid4() for _ in range(count)]
    async with async_session_factory() as session:
        for i, entity_id in enumerate(entity_ids):
            session.add(
                AuditLog(
                    account_id=account_id,
                    actor_user_id=actor_id,
                    action="contact.created",
                    entity_type="contact",
                    entity_id=entity_id,
                    event_metadata={},
                    created_at=base - timedelta(seconds=i),
                )
            )
        await session.commit()
    return entity_ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_audit_logs_default_page_size_is_bounded(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Audit Page Admin", role_name="Admin", account_id=account_id
    )
    await _seed_audit_logs(account_id, admin_id, DEFAULT_LIMIT + 10)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.get("/audit")

    assert response.status_code == 200
    assert len(response.json()) == DEFAULT_LIMIT

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == admin_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_audit_logs_huge_limit_is_clamped_not_honored(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    admin_id = await user_factory(
        full_name="Audit Clamp Admin", role_name="Admin", account_id=account_id
    )
    await _seed_audit_logs(account_id, admin_id, MAX_LIMIT + 10)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.get("/audit", params={"limit": 100_000})

    assert response.status_code == 200
    assert len(response.json()) == MAX_LIMIT

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == admin_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_audit_logs_offset_skips_rows_and_respects_account_isolation(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Audit Offset Admin A", role_name="Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Audit Offset Admin B", role_name="Admin", account_id=account_b
    )
    await _seed_audit_logs(account_a, admin_a, 12)
    account_b_entity_ids = await _seed_audit_logs(account_b, admin_b, 12)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
    ) as client:
        page1 = await client.get("/audit", params={"limit": 5, "offset": 0})
        page2 = await client.get("/audit", params={"limit": 5, "offset": 5})
        # Offset past account A's own 12 rows -- must never spill into account B's rows.
        far_page = await client.get("/audit", params={"limit": 50, "offset": 5})

    assert page1.status_code == 200
    assert page2.status_code == 200
    page1_ids = {row["id"] for row in page1.json()}
    page2_ids = {row["id"] for row in page2.json()}
    assert len(page1_ids) == 5
    assert len(page2_ids) == 5
    # offset genuinely skips rows at the SQL level, not a truncation of the same page.
    assert page1_ids.isdisjoint(page2_ids)

    far_page_entity_ids = {row["entity_id"] for row in far_page.json()}
    assert far_page_entity_ids.isdisjoint({str(eid) for eid in account_b_entity_ids})

    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(AuditLog.actor_user_id.in_([admin_a, admin_b]))
        )
        await session.commit()
