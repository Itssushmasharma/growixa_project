"""CSV contact import integration tests (GRX-CONTACT-004).

Integration-tier: exercises real Postgres, the real create_app() app, and the real seeded
roles from GRX-AUTH-001. Rows created by a test are cleaned up by that test.
"""

import json
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
    ContactCustomField,
    ContactFieldValue,
    ContactImport,
    ContactImportRow,
)
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


def _csv_file(content: str) -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("contacts.csv", content.encode("utf-8"), "text/csv")}


async def _cleanup_contacts_by_email(*emails: str) -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(Contact.id).where(Contact.email.in_(emails)))
        contact_ids = [row[0] for row in result.all()]
        for contact_id in contact_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "contact", AuditLog.entity_id == contact_id
                )
            )
            await session.execute(
                delete(ContactFieldValue).where(ContactFieldValue.contact_id == contact_id)
            )
        await session.execute(delete(Contact).where(Contact.email.in_(emails)))
        await session.commit()


async def _cleanup_import(import_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(
                AuditLog.entity_type == "contact_import", AuditLog.entity_id == import_id
            )
        )
        await session.execute(
            delete(ContactImportRow).where(ContactImportRow.import_id == import_id)
        )
        await session.execute(delete(ContactImport).where(ContactImport.id == import_id))
        await session.commit()


async def _cleanup_custom_field(key: str) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(ContactCustomField).where(ContactCustomField.key == key))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_import_csv_creating_and_updating_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    existing_email = f"{uuid.uuid4()}@example.com"
    new_email = f"{uuid.uuid4()}@example.com"
    mapping = {"Email": "email", "First": "first_name"}

    transport = ASGITransport(app=create_app())
    import_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            precreate = await client.post(
                "/contacts", json={"email": existing_email, "first_name": "Old"}
            )
            assert precreate.status_code == 201

            csv_content = f"Email,First\n{existing_email},Updated\n{new_email},Brand New\n"
            response = await client.post(
                "/contacts/imports",
                files=_csv_file(csv_content),
                data={"column_mapping": json.dumps(mapping)},
            )
            assert response.status_code == 201
            body = response.json()
            import_id = uuid.UUID(body["id"])
            assert body["status"] == "COMPLETED"
            assert body["total_rows"] == 2
            assert body["imported_count"] == 1
            assert body["updated_count"] == 1
            assert body["skipped_count"] == 0
            assert body["error_count"] == 0

            rows_resp = await client.get(f"/contacts/imports/{import_id}/rows")
            rows = rows_resp.json()
            assert {r["email"]: r["status"] for r in rows} == {
                existing_email: "UPDATED",
                new_email: "IMPORTED",
            }

            updated_contact = await client.get("/contacts")
            emails = {c["email"]: c["first_name"] for c in updated_contact.json()}
            assert emails[existing_email] == "Updated"
            assert emails[new_email] == "Brand New"
    finally:
        if import_id is not None:
            await _cleanup_import(import_id)
        await _cleanup_contacts_by_email(existing_email, new_email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_import_maps_custom_field_column(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"
    field_key = f"plan-{uuid.uuid4().hex[:8]}"
    mapping = {"Email": "email", "Plan": f"custom_field:{field_key}"}

    transport = ASGITransport(app=create_app())
    import_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            field_resp = await client.post(
                "/contacts/custom-fields",
                json={"key": field_key, "label": "Plan", "field_type": "TEXT"},
            )
            assert field_resp.status_code == 201

            csv_content = f"Email,Plan\n{email},Enterprise\n"
            response = await client.post(
                "/contacts/imports",
                files=_csv_file(csv_content),
                data={"column_mapping": json.dumps(mapping)},
            )
            assert response.status_code == 201
            import_id = uuid.UUID(response.json()["id"])
            assert response.json()["imported_count"] == 1

            contacts = (await client.get("/contacts")).json()
            match = next(c for c in contacts if c["email"] == email)
            assert match["custom_fields"][field_key] == "Enterprise"
    finally:
        if import_id is not None:
            await _cleanup_import(import_id)
        await _cleanup_contacts_by_email(email)
        await _cleanup_custom_field(field_key)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_import_skips_blank_rows_and_flags_missing_email(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    valid_email = f"{uuid.uuid4()}@example.com"
    mapping = {"Email": "email", "First": "first_name"}

    transport = ASGITransport(app=create_app())
    import_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            csv_content = f"Email,First\n,\n{valid_email},Ok\n,Missing Email\n"
            response = await client.post(
                "/contacts/imports",
                files=_csv_file(csv_content),
                data={"column_mapping": json.dumps(mapping)},
            )
            assert response.status_code == 201
            body = response.json()
            import_id = uuid.UUID(body["id"])
            assert body["total_rows"] == 3
            assert body["imported_count"] == 1
            assert body["skipped_count"] == 1
            assert body["error_count"] == 1

            rows = (await client.get(f"/contacts/imports/{import_id}/rows")).json()
            statuses = [r["status"] for r in rows]
            assert statuses == ["SKIPPED", "IMPORTED", "ERROR"]
            assert rows[2]["error_message"] == "Missing required email value"
    finally:
        if import_id is not None:
            await _cleanup_import(import_id)
        await _cleanup_contacts_by_email(valid_email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_import_rejects_mapping_without_email(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    mapping = {"First": "first_name"}

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/imports",
            files=_csv_file("First\nAlice\n"),
            data={"column_mapping": json.dumps(mapping)},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_import_rejects_unknown_custom_field_key_in_mapping(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    mapping = {"Email": "email", "Plan": "custom_field:does-not-exist"}

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/imports",
            files=_csv_file("Email,Plan\na@example.com,Pro\n"),
            data={"column_mapping": json.dumps(mapping)},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_list_and_get_import_history(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email = f"{uuid.uuid4()}@example.com"
    mapping = {"Email": "email"}

    transport = ASGITransport(app=create_app())
    import_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_resp = await client.post(
                "/contacts/imports",
                files=_csv_file(f"Email\n{email}\n"),
                data={"column_mapping": json.dumps(mapping)},
            )
            import_id = uuid.UUID(create_resp.json()["id"])

            list_resp = await client.get("/contacts/imports")
            assert any(item["id"] == str(import_id) for item in list_resp.json())

            get_resp = await client.get(f"/contacts/imports/{import_id}")
            assert get_resp.status_code == 200
            assert get_resp.json()["filename"] == "contacts.csv"

            missing_resp = await client.get(f"/contacts/imports/{uuid.uuid4()}")
            assert missing_resp.status_code == 404
    finally:
        if import_id is not None:
            await _cleanup_import(import_id)
        await _cleanup_contacts_by_email(email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_can_view_but_not_create_imports(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        list_response = await client.get("/contacts/imports")
        create_response = await client.post(
            "/contacts/imports",
            files=_csv_file("Email\na@example.com\n"),
            data={"column_mapping": json.dumps({"Email": "email"})},
        )

    assert list_response.status_code == 200
    assert create_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_has_no_access_to_imports(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.get("/contacts/imports")

    assert response.status_code == 403
