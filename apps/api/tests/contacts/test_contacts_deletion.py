"""Contact deletion and soft-delete semantics tests (GRX-CONTACT-010, DEC-GRX-034).

Integration-tier: exercises real Postgres, the real create_app() app, and the real seeded
roles from GRX-AUTH-001 / GRX-SAAS-001. Contact rows created by tests are cleaned up by tests.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.config import get_settings
from growixa_api.contacts.models import (
    Contact,
    ContactFieldValue,
    ContactList,
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
async def test_manager_can_delete_single_contact(
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
            delete_resp = await client.delete(f"/contacts/{contact_id}")
            assert delete_resp.status_code == 204

            # 3. GET by ID returns 404
            get_resp = await client.get(f"/contacts/{contact_id}")
            assert get_resp.status_code == 404

            # 4. GET /contacts list does not include the contact
            list_resp = await client.get("/contacts")
            assert list_resp.status_code == 200
            assert not any(c["id"] == str(contact_id) for c in list_resp.json())

            # 5. Database row still exists with deleted_at set (DEC-GRX-034 soft delete)
            async with async_session_factory() as session:
                row = await session.get(Contact, contact_id)
                assert row is not None
                assert row.deleted_at is not None

                # 6. Audit log recorded
                audit_result = await session.execute(
                    select(AuditLog).where(
                        AuditLog.entity_type == "contact",
                        AuditLog.entity_id == contact_id,
                        AuditLog.action == "contact.deleted",
                    )
                )
                audit_entry = audit_result.scalar_one_or_none()
                assert audit_entry is not None
                assert audit_entry.actor_user_id == manager_id
                assert audit_entry.event_metadata["email"] == email.lower()
    finally:
        if contact_id is not None:
            await _cleanup_contacts(contact_id, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deleting_nonexistent_or_already_deleted_contact_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    random_id = uuid.uuid4()

    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
    ) as client:
        # Non-existent contact
        resp = await client.delete(f"/contacts/{random_id}")
        assert resp.status_code == 404

        # Create, delete once, then delete again
        create_resp = await client.post("/contacts", json={"email": f"{uuid.uuid4()}@example.com"})
        c_id = uuid.UUID(create_resp.json()["id"])
        try:
            first_del = await client.delete(f"/contacts/{c_id}")
            assert first_del.status_code == 204

            second_del = await client.delete(f"/contacts/{c_id}")
            assert second_del.status_code == 404
        finally:
            await _cleanup_contacts(c_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reimport_or_recreate_same_email_after_soft_delete_creates_fresh_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Proves DEC-GRX-034 Section 3: partial unique index permits creating a new contact
    with the same email without unique constraint collision against the soft-deleted row."""
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    first_id: uuid.UUID | None = None
    second_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # 1. Create first contact
            resp1 = await client.post(
                "/contacts", json={"email": email, "first_name": "First Instance"}
            )
            assert resp1.status_code == 201
            first_id = uuid.UUID(resp1.json()["id"])

            # 2. Delete it
            del_resp = await client.delete(f"/contacts/{first_id}")
            assert del_resp.status_code == 204

            # 3. Create contact again with same email -> creates fresh contact
            resp2 = await client.post(
                "/contacts", json={"email": email, "first_name": "Second Fresh Instance"}
            )
            assert resp2.status_code == 201
            second_id = uuid.UUID(resp2.json()["id"])
            assert second_id != first_id

            # 4. Verify both exist in DB: first is soft-deleted, second is live
            async with async_session_factory() as session:
                c1 = await session.get(Contact, first_id)
                c2 = await session.get(Contact, second_id)
                assert c1 is not None and c1.deleted_at is not None
                assert c2 is not None and c2.deleted_at is None
    finally:
        cleanups = [c for c in (first_id, second_id) if c is not None]
        if cleanups:
            await _cleanup_contacts(*cleanups)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_delete_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    created_ids: list[uuid.UUID] = []

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # Create 3 contacts
            for i in range(3):
                r = await client.post(
                    "/contacts",
                    json={"email": f"{uuid.uuid4()}@example.com", "first_name": f"Bulk {i}"},
                )
                assert r.status_code == 201
                created_ids.append(uuid.UUID(r.json()["id"]))

            # Bulk delete 2 of them
            to_delete = created_ids[:2]
            bulk_resp = await client.post(
                "/contacts/bulk-delete",
                json={"contact_ids": [str(c_id) for c_id in to_delete]},
            )
            assert bulk_resp.status_code == 200
            assert bulk_resp.json() == {"deleted_count": 2}

            # Verify list only contains the 3rd
            list_resp = await client.get("/contacts")
            visible_ids = {c["id"] for c in list_resp.json()}
            assert str(created_ids[0]) not in visible_ids
            assert str(created_ids[1]) not in visible_ids
            assert str(created_ids[2]) in visible_ids
    finally:
        if created_ids:
            await _cleanup_contacts(*created_ids, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_purge_all_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    created_ids: list[uuid.UUID] = []

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # Create 3 contacts
            for _ in range(3):
                r = await client.post("/contacts", json={"email": f"{uuid.uuid4()}@example.com"})
                assert r.status_code == 201
                created_ids.append(uuid.UUID(r.json()["id"]))

            # Purge all
            purge_resp = await client.delete("/contacts/all")
            assert purge_resp.status_code == 200
            assert purge_resp.json()["deleted_count"] >= 3

            # List is now empty
            list_resp = await client.get("/contacts")
            assert list_resp.status_code == 200
            assert list_resp.json() == []
    finally:
        if created_ids:
            await _cleanup_contacts(*created_ids, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rbac_analyst_cannot_delete_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None

    try:
        # Create contact as manager
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            r = await client.post("/contacts", json={"email": f"{uuid.uuid4()}@example.com"})
            assert r.status_code == 201
            contact_id = uuid.UUID(r.json()["id"])

        # Attempt deletions as analyst
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
        ) as client:
            del_resp = await client.delete(f"/contacts/{contact_id}")
            assert del_resp.status_code == 403

            bulk_resp = await client.post(
                "/contacts/bulk-delete", json={"contact_ids": [str(contact_id)]}
            )
            assert bulk_resp.status_code == 403

            purge_resp = await client.delete("/contacts/all")
            assert purge_resp.status_code == 403
    finally:
        if contact_id is not None:
            await _cleanup_contacts(contact_id, actor_id=manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.delete(f"/contacts/{uuid.uuid4()}")).status_code == 401
        assert (
            await client.post("/contacts/bulk-delete", json={"contact_ids": []})
        ).status_code == 401
        assert (await client.delete("/contacts/all")).status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_segment_and_list_member_queries_exclude_deleted_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Proves DEC-GRX-034 Section 5.3: segment membership and list queries exclude deleted rows."""
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    contact_ids: list[uuid.UUID] = []
    list_id: uuid.UUID | None = None

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # 1. Create a list
            list_resp = await client.post("/contacts/lists", json={"name": f"List {uuid.uuid4()}"})
            assert list_resp.status_code == 201
            list_id = uuid.UUID(list_resp.json()["id"])

            # 2. Create two contacts and add both to the list
            r1 = await client.post("/contacts", json={"email": f"{uuid.uuid4()}@example.com"})
            r2 = await client.post("/contacts", json={"email": f"{uuid.uuid4()}@example.com"})
            id1 = uuid.UUID(r1.json()["id"])
            id2 = uuid.UUID(r2.json()["id"])
            contact_ids.extend([id1, id2])

            await client.post(f"/contacts/lists/{list_id}/members", json={"contact_id": str(id1)})
            await client.post(f"/contacts/lists/{list_id}/members", json={"contact_id": str(id2)})

            # List count should be 2
            list_detail = await client.get(f"/contacts/lists/{list_id}")
            assert list_detail.json()["member_count"] == 2

            # 3. Soft delete the first contact
            del_r = await client.delete(f"/contacts/{id1}")
            assert del_r.status_code == 204

            # 4. List count should now be 1
            list_detail_after = await client.get(f"/contacts/lists/{list_id}")
            assert list_detail_after.json()["member_count"] == 1
    finally:
        if contact_ids:
            await _cleanup_contacts(*contact_ids, actor_id=manager_id)
        if list_id is not None:
            async with async_session_factory() as session:
                await session.execute(
                    delete(ContactListMember).where(ContactListMember.list_id == list_id)
                )
                await session.execute(delete(ContactList).where(ContactList.id == list_id))
                await session.commit()
