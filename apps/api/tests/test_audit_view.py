"""Audit log viewing endpoint tests (GRX-AUDIT-002).

Integration-tier: exercises real Postgres and the real create_app() app, using the shared
user_factory fixture (conftest.py) plus directly-inserted audit_logs rows.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.audit.services import record_event
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_list_audit_logs(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Audit Admin", role_name="Admin")
    entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        await record_event(
            session,
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
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Audit Admin", role_name="Admin")
    contact_entity_id = uuid.uuid4()
    user_entity_id = uuid.uuid4()
    async with async_session_factory() as session:
        await record_event(
            session,
            actor_user_id=admin_id,
            action="contact.created",
            entity_type="contact",
            entity_id=contact_entity_id,
            metadata={},
        )
        await record_event(
            session,
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
