"""Audit log write/list tests (GRX-AUDIT-001).

Integration-tier: exercises real Postgres. Uses a throwaway user as the actor for one case,
and actor_user_id=None (a system event, explicitly allowed per DATABASE_SCHEMA.md) for
another.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import delete

from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import list_events, record_event
from growixa_api.db import async_session_factory
from growixa_api.users.models import User


@pytest.fixture
async def actor_user_id() -> AsyncGenerator[uuid.UUID, None]:
    async with async_session_factory() as session:
        user = User(email=f"{uuid.uuid4()}@example.com", password_hash="x", full_name="Test Actor")
        session.add(user)
        await session.flush()
        await session.commit()
        user_id = user.id

    yield user_id

    async with async_session_factory() as session:
        # actor_user_id has no ON DELETE CASCADE (an audit trail must survive the actor
        # being removed) — clean up this test's audit rows before the user itself.
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.mark.asyncio
async def test_record_event_then_list_events_round_trips(actor_user_id: uuid.UUID) -> None:
    entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        recorded = await record_event(
            session,
            actor_user_id=actor_user_id,
            action="user.login",
            entity_type="user",
            entity_id=entity_id,
            metadata={"ip_hint": "office"},
        )
        await session.commit()

    async with async_session_factory() as session:
        events = await list_events(session, entity_type="user", entity_id=entity_id)

    assert len(events) == 1
    event = events[0]
    assert event.id == recorded.id
    assert event.actor_user_id == actor_user_id
    assert event.action == "user.login"
    assert event.entity_type == "user"
    assert event.entity_id == entity_id
    assert event.event_metadata == {"ip_hint": "office"}


@pytest.mark.asyncio
async def test_record_event_allows_system_actor() -> None:
    entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        await record_event(
            session,
            actor_user_id=None,
            action="system.healthcheck",
            entity_type="system",
            entity_id=entity_id,
            metadata={},
        )
        await session.commit()

    async with async_session_factory() as session:
        events = await list_events(session, entity_type="system", entity_id=entity_id)

    assert len(events) == 1
    assert events[0].actor_user_id is None


@pytest.mark.asyncio
async def test_record_event_redacts_sensitive_metadata_keys(actor_user_id: uuid.UUID) -> None:
    entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        await record_event(
            session,
            actor_user_id=actor_user_id,
            action="user.password_reset_completed",
            entity_type="user",
            entity_id=entity_id,
            metadata={
                "password": "hunter2",
                "password_hash": "$argon2id$...",
                "token": "raw-token-value",
                "safe_field": "kept",
            },
        )
        await session.commit()

    async with async_session_factory() as session:
        events = await list_events(session, entity_type="user", entity_id=entity_id)

    assert events[0].event_metadata == {
        "password": "[REDACTED]",
        "password_hash": "[REDACTED]",
        "token": "[REDACTED]",
        "safe_field": "kept",
    }
