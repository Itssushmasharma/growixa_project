"""Audit log write/list tests (GRX-AUDIT-001).

Integration-tier: exercises real Postgres. Uses a throwaway user (via the shared
user_factory fixture) as the actor for two cases, and actor_user_id=None (a system event,
explicitly allowed per DATABASE_SCHEMA.md) for another.

Each test that attributes an event to a factory-created user deletes its own audit_logs
rows before returning — user_factory's teardown deletes the user, and actor_user_id has no
ON DELETE CASCADE (an audit trail must survive the actor being removed), so leftover rows
would otherwise turn that teardown into a foreign-key violation.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import delete

from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import list_events, record_event
from growixa_api.db import async_session_factory


@pytest.mark.asyncio
@pytest.mark.integration
async def test_record_event_then_list_events_round_trips(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    actor_user_id = await user_factory(full_name="Test Actor")
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

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == actor_user_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
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

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.entity_id == entity_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_record_event_redacts_sensitive_metadata_keys(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    actor_user_id = await user_factory(full_name="Test Actor")
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

    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == actor_user_id))
        await session.commit()
