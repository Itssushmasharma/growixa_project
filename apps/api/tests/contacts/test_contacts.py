"""Contacts CRUD, dedup, custom fields, and permission-split tests (GRX-CONTACT-001).

Integration-tier: exercises real Postgres, the real create_app() app, and the real seeded
roles from GRX-AUTH-001. Contact rows created by a test are cleaned up by that test (via
_cleanup_contact), since `contacts` isn't a singleton table like company_profile.
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
from growixa_api.contacts.models import Contact, ContactCustomField, ContactFieldValue
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
            await session.execute(
                delete(ContactFieldValue).where(ContactFieldValue.contact_id == contact_id)
            )
            await session.execute(delete(Contact).where(Contact.id == contact_id))
        await session.commit()


async def _cleanup_custom_field(key: str) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(ContactCustomField).where(ContactCustomField.key == key))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_a_contact(
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
            response = await client.post("/contacts", json={"email": email, "first_name": "Ada"})
            assert response.status_code == 201
            body = response.json()
            assert body["email"] == email.lower()
            assert body["first_name"] == "Ada"
            assert body["status"] == "ACTIVE"
            contact_id = uuid.UUID(body["id"])
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_creating_with_an_existing_email_updates_instead_of_duplicating(
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
            first = await client.post("/contacts", json={"email": email, "first_name": "Old"})
            second = await client.post("/contacts", json={"email": email, "first_name": "New"})

            assert first.status_code == 201
            assert second.status_code == 201
            assert first.json()["id"] == second.json()["id"]
            assert second.json()["first_name"] == "New"

            list_response = await client.get("/contacts")
            matching = [c for c in list_response.json() if c["email"] == email.lower()]
            assert len(matching) == 1

            contact_id = uuid.UUID(second.json()["id"])
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_can_view_but_not_create_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        list_response = await client.get("/contacts")
        create_response = await client.post("/contacts", json={"email": "x@example.com"})

    assert list_response.status_code == 200
    assert create_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_has_no_contacts_access_at_all(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        list_response = await client.get("/contacts")
        create_response = await client.post("/contacts", json={"email": "x@example.com"})

    assert list_response.status_code == 403
    assert create_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/contacts")
        create_response = await client.post("/contacts", json={"email": "x@example.com"})

    assert list_response.status_code == 401
    assert create_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_edit_a_contacts_fields(
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
            created = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(created.json()["id"])

            updated = await client.patch(f"/contacts/{contact_id}", json={"phone": "+1-555-0100"})

        assert updated.status_code == 200
        assert updated.json()["phone"] == "+1-555-0100"
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_editing_email_to_match_another_contact_conflicts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email_a = f"{uuid.uuid4()}@example.com"
    email_b = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_a_id: uuid.UUID | None = None
    contact_b_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            resp_a = await client.post("/contacts", json={"email": email_a})
            resp_b = await client.post("/contacts", json={"email": email_b})
            contact_a_id = uuid.UUID(resp_a.json()["id"])
            contact_b_id = uuid.UUID(resp_b.json()["id"])

            conflict = await client.patch(f"/contacts/{contact_a_id}", json={"email": email_b})

        assert conflict.status_code == 409
    finally:
        for cid in (contact_a_id, contact_b_id):
            if cid is not None:
                await _cleanup_contact(cid)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_archiving_and_reactivating_a_contact(
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
            created = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(created.json()["id"])

            archived = await client.patch(
                f"/contacts/{contact_id}/status", json={"status": "ARCHIVED"}
            )
            assert archived.status_code == 200
            assert archived.json()["status"] == "ARCHIVED"

            reactivated = await client.patch(
                f"/contacts/{contact_id}/status", json={"status": "ACTIVE"}
            )
            assert reactivated.status_code == 200
            assert reactivated.json()["status"] == "ACTIVE"

        async with async_session_factory() as session:
            result = await session.execute(
                select(AuditLog.action).where(
                    AuditLog.entity_type == "contact", AuditLog.entity_id == contact_id
                )
            )
            actions = {row[0] for row in result.all()}
        assert "contact.archived" in actions
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_custom_field_can_be_created_and_set_on_a_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    field_key = f"field_{uuid.uuid4().hex[:8]}"
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            field_response = await client.post(
                "/contacts/custom-fields",
                json={"key": field_key, "label": "Company size", "field_type": "TEXT"},
            )
            assert field_response.status_code == 201

            contact_response = await client.post(
                "/contacts",
                json={"email": email, "custom_fields": {field_key: "50-100"}},
            )
            assert contact_response.status_code == 201
            assert contact_response.json()["custom_fields"] == {field_key: "50-100"}
            contact_id = uuid.UUID(contact_response.json()["id"])

            get_response = await client.get(f"/contacts/{contact_id}")
            assert get_response.json()["custom_fields"] == {field_key: "50-100"}
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)
        await _cleanup_custom_field(field_key)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_creating_a_contact_with_an_unknown_custom_field_key_fails(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts", json={"email": email, "custom_fields": {"does_not_exist": "x"}}
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_custom_field_key_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    field_key = f"field_{uuid.uuid4().hex[:8]}"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            first = await client.post(
                "/contacts/custom-fields",
                json={"key": field_key, "label": "First", "field_type": "TEXT"},
            )
            second = await client.post(
                "/contacts/custom-fields",
                json={"key": field_key, "label": "Second", "field_type": "TEXT"},
            )

        assert first.status_code == 201
        assert second.status_code == 409
    finally:
        await _cleanup_custom_field(field_key)
