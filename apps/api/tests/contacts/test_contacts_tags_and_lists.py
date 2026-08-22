"""Tags and lists integration tests (GRX-CONTACT-002).

Integration-tier: exercises real Postgres, the real create_app() app, and the real seeded
roles from GRX-AUTH-001. Rows created by a test are cleaned up by that test.
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
    ContactList,
    ContactListMember,
    ContactTag,
    Tag,
)
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_contact(*contact_ids: uuid.UUID) -> None:
    async with async_session_factory() as session:
        for contact_id in contact_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "contact", AuditLog.entity_id == contact_id
                )
            )
            await session.execute(delete(ContactTag).where(ContactTag.contact_id == contact_id))
            await session.execute(
                delete(ContactListMember).where(ContactListMember.contact_id == contact_id)
            )
            await session.execute(delete(Contact).where(Contact.id == contact_id))
        await session.commit()


async def _cleanup_tag(name: str) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(Tag).where(Tag.name == name))
        await session.commit()


async def _cleanup_list(list_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(ContactListMember).where(ContactListMember.list_id == list_id))
        await session.execute(delete(ContactList).where(ContactList.id == list_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_and_list_tags(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    tag_name = f"tag-{uuid.uuid4().hex[:8]}"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post("/contacts/tags", json={"name": tag_name})
            assert create_response.status_code == 201

            list_response = await client.get("/contacts/tags")
            names = [t["name"] for t in list_response.json()]
            assert tag_name in names
    finally:
        await _cleanup_tag(tag_name)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_tag_name_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    tag_name = f"tag-{uuid.uuid4().hex[:8]}"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            first = await client.post("/contacts/tags", json={"name": tag_name})
            second = await client.post("/contacts/tags", json={"name": tag_name})

        assert first.status_code == 201
        assert second.status_code == 409
    finally:
        await _cleanup_tag(tag_name)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_attaching_and_detaching_a_tag_on_a_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"
    tag_name = f"tag-{uuid.uuid4().hex[:8]}"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])
            tag_resp = await client.post("/contacts/tags", json={"name": tag_name})
            tag_id = tag_resp.json()["id"]

            attach_resp = await client.post(f"/contacts/{contact_id}/tags", json={"tag_id": tag_id})
            assert attach_resp.status_code == 200
            assert attach_resp.json()["tags"] == [tag_name]

            get_resp = await client.get(f"/contacts/{contact_id}")
            assert get_resp.json()["tags"] == [tag_name]

            detach_resp = await client.delete(f"/contacts/{contact_id}/tags/{tag_id}")
            assert detach_resp.status_code == 200
            assert detach_resp.json()["tags"] == []
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)
        await _cleanup_tag(tag_name)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_attaching_an_unknown_tag_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])

            response = await client.post(
                f"/contacts/{contact_id}/tags", json={"tag_id": str(uuid.uuid4())}
            )
        assert response.status_code == 404
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_a_list_and_add_remove_members(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    list_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])

            list_resp = await client.post(
                "/contacts/lists", json={"name": "VIP customers", "description": "Top tier"}
            )
            assert list_resp.status_code == 201
            assert list_resp.json()["member_count"] == 0
            list_id = uuid.UUID(list_resp.json()["id"])

            add_resp = await client.post(
                f"/contacts/lists/{list_id}/members", json={"contact_id": str(contact_id)}
            )
            assert add_resp.status_code == 200
            assert add_resp.json()["member_count"] == 1

            get_resp = await client.get(f"/contacts/lists/{list_id}")
            assert get_resp.json()["member_count"] == 1

            remove_resp = await client.delete(f"/contacts/lists/{list_id}/members/{contact_id}")
            assert remove_resp.status_code == 200
            assert remove_resp.json()["member_count"] == 0
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)
        if list_id is not None:
            await _cleanup_list(list_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_can_view_but_not_create_tags_or_lists(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        tags_response = await client.get("/contacts/tags")
        lists_response = await client.get("/contacts/lists")
        create_tag_response = await client.post("/contacts/tags", json={"name": "x"})
        create_list_response = await client.post("/contacts/lists", json={"name": "x"})

    assert tags_response.status_code == 200
    assert lists_response.status_code == 200
    assert create_tag_response.status_code == 403
    assert create_list_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_has_no_access_to_tags_or_lists(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        tags_response = await client.get("/contacts/tags")
        lists_response = await client.get("/contacts/lists")

    assert tags_response.status_code == 403
    assert lists_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_get_list_members(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    list_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            contact_resp = await client.post(
                "/contacts", json={"email": email, "first_name": "Alice", "last_name": "Smith"}
            )
            assert contact_resp.status_code == 201
            contact_id = uuid.UUID(contact_resp.json()["id"])

            list_resp = await client.post("/contacts/lists", json={"name": "VIP Customers"})
            assert list_resp.status_code == 201
            list_id = uuid.UUID(list_resp.json()["id"])

            add_resp = await client.post(
                f"/contacts/lists/{list_id}/members", json={"contact_id": str(contact_id)}
            )
            assert add_resp.status_code == 200

            members_resp = await client.get(f"/contacts/lists/{list_id}/members")
            assert members_resp.status_code == 200
            members_data = members_resp.json()
            assert len(members_data) == 1
            assert members_data[0]["id"] == str(contact_id)
            assert members_data[0]["email"] == email
            assert members_data[0]["first_name"] == "Alice"
            assert members_data[0]["last_name"] == "Smith"
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)
        if list_id is not None:
            await _cleanup_list(list_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_list_members_for_nonexistent_list_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
    ) as client:
        resp = await client.get(f"/contacts/lists/{uuid.uuid4()}/members")
        assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_list_members_cross_account_isolation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_a = await user_factory(full_name="Manager A", role_name="Marketing Manager")
    manager_b = await user_factory(full_name="Manager B", role_name="Marketing Manager")

    email = f"{uuid.uuid4()}@example.com"
    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    list_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_a)
        ) as client_a:
            contact_resp = await client_a.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])

            list_resp = await client_a.post("/contacts/lists", json={"name": "Account A List"})
            list_id = uuid.UUID(list_resp.json()["id"])

            await client_a.post(
                f"/contacts/lists/{list_id}/members", json={"contact_id": str(contact_id)}
            )

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_b)
        ) as client_b:
            # Manager B from another account cannot access Account A's list members
            foreign_resp = await client_b.get(f"/contacts/lists/{list_id}/members")
            assert foreign_resp.status_code == 404
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)
        if list_id is not None:
            await _cleanup_list(list_id)
