"""Contact restoration semantics and quota checks (GRX-CONTACT-016).

Integration-tier: exercises real Postgres, the real create_app() app, and the real seeded
roles from GRX-AUTH-001 / GRX-SAAS-001. Contact rows created by tests are cleaned up by tests.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.config import get_settings
from growixa_api.contacts.models import (
    Contact,
    ContactFieldValue,
    ContactListMember,
    ContactTag,
)
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_contacts(*contact_ids: uuid.UUID, actor_id: uuid.UUID | None = None) -> None:
    async with async_session_factory() as session:
        if actor_id is not None:
            await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == actor_id))
        for contact_id in contact_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "contact", AuditLog.entity_id == contact_id
                )
            )
            await session.execute(
                delete(ContactFieldValue).where(ContactFieldValue.contact_id == contact_id)
            )
            await session.execute(delete(ContactTag).where(ContactTag.contact_id == contact_id))
            await session.execute(
                delete(ContactListMember).where(ContactListMember.contact_id == contact_id)
            )
            await session.execute(delete(Contact).where(Contact.id == contact_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_list_deleted_contacts_and_restore_single(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # 1. Create contact
            create_resp = await client.post("/contacts", json={"email": email, "first_name": "Ada"})
            assert create_resp.status_code == 201
            contact_id = uuid.UUID(create_resp.json()["id"])

            # 2. Delete contact
            del_resp = await client.delete(f"/contacts/{contact_id}")
            assert del_resp.status_code == 204

            # 3. Default GET /contacts should NOT return it
            list_resp = await client.get("/contacts")
            assert list_resp.status_code == 200
            ids = [c["id"] for c in list_resp.json()]
            assert str(contact_id) not in ids

            # 4. GET /contacts?deleted_only=true returns the deleted contact
            deleted_list_resp = await client.get("/contacts?deleted_only=true")
            assert deleted_list_resp.status_code == 200
            deleted_ids = [c["id"] for c in deleted_list_resp.json()]
            assert str(contact_id) in deleted_ids
            deleted_item = next(c for c in deleted_list_resp.json() if c["id"] == str(contact_id))
            assert deleted_item["deleted_at"] is not None

            # 5. Restore contact
            restore_resp = await client.post(f"/contacts/{contact_id}/restore")
            assert restore_resp.status_code == 200
            restored_data = restore_resp.json()
            assert restored_data["id"] == str(contact_id)
            assert restored_data["deleted_at"] is None

            # 6. Default GET /contacts now returns the restored contact
            active_list_resp = await client.get("/contacts")
            assert active_list_resp.status_code == 200
            active_ids = [c["id"] for c in active_list_resp.json()]
            assert str(contact_id) in active_ids
    finally:
        if contact_id is not None:
            await _cleanup_contacts(contact_id, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_restore_conflict_with_active_duplicate_email(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    shared_email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    old_contact_id: uuid.UUID | None = None
    new_contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # 1. Create first contact and delete it
            create1 = await client.post(
                "/contacts", json={"email": shared_email, "first_name": "Old"}
            )
            assert create1.status_code == 201
            old_contact_id = uuid.UUID(create1.json()["id"])

            del1 = await client.delete(f"/contacts/{old_contact_id}")
            assert del1.status_code == 204

            # 2. Create second contact with the same email (allowed by partial unique index)
            create2 = await client.post(
                "/contacts", json={"email": shared_email, "first_name": "New"}
            )
            assert create2.status_code == 201
            new_contact_id = uuid.UUID(create2.json()["id"])

            # 3. Attempting to restore old contact should return 409 Conflict
            restore_resp = await client.post(f"/contacts/{old_contact_id}/restore")
            assert restore_resp.status_code == 409
            assert "already exists" in restore_resp.json()["detail"]
    finally:
        ids = [i for i in (old_contact_id, new_contact_id) if i is not None]
        if ids:
            await _cleanup_contacts(*ids, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_bulk_restore_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email1 = f"{uuid.uuid4()}@example.com"
    email2 = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    id1: uuid.UUID | None = None
    id2: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            c1 = await client.post("/contacts", json={"email": email1, "first_name": "One"})
            c2 = await client.post("/contacts", json={"email": email2, "first_name": "Two"})
            assert c1.status_code == 201 and c2.status_code == 201
            id1 = uuid.UUID(c1.json()["id"])
            id2 = uuid.UUID(c2.json()["id"])

            # Bulk delete both
            del_resp = await client.post(
                "/contacts/bulk-delete",
                json={"contact_ids": [str(id1), str(id2)]},
            )
            assert del_resp.status_code == 200
            assert del_resp.json()["deleted_count"] == 2

            # Bulk restore both
            restore_resp = await client.post(
                "/contacts/bulk-restore",
                json={"contact_ids": [str(id1), str(id2)]},
            )
            assert restore_resp.status_code == 200
            assert restore_resp.json()["restored_count"] == 2

            # Verify active list contains both
            active_list = await client.get("/contacts")
            assert active_list.status_code == 200
            active_ids = [c["id"] for c in active_list.json()]
            assert str(id1) in active_ids
            assert str(id2) in active_ids
    finally:
        ids = [i for i in (id1, id2) if i is not None]
        if ids:
            await _cleanup_contacts(*ids, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_cannot_restore_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")
    dummy_id = uuid.uuid4()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        single_restore = await client.post(f"/contacts/{dummy_id}/restore")
        assert single_restore.status_code == 403

        bulk_restore = await client.post(
            "/contacts/bulk-restore", json={"contact_ids": [str(dummy_id)]}
        )
        assert bulk_restore.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_cannot_restore_contact() -> None:
    transport = ASGITransport(app=create_app())
    dummy_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(f"/contacts/{dummy_id}/restore")
        assert resp.status_code == 401
