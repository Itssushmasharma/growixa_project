# ruff: noqa: E501

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
    ConsentRecord,
    Contact,
    ContactActivity,
    CRMCompany,
    SuppressionEntry,
)
from growixa_api.contacts.services import detect_csv_columns_service
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_user_artifacts(*user_ids: uuid.UUID) -> None:
    async with async_session_factory() as session:
        for uid in user_ids:
            await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == uid))
            await session.execute(
                delete(SuppressionEntry).where(SuppressionEntry.suppressed_by_user_id == uid)
            )
            await session.execute(
                delete(ContactActivity).where(ContactActivity.created_by_user_id == uid)
            )
            await session.execute(delete(CRMCompany).where(CRMCompany.created_by_user_id == uid))
            await session.execute(delete(Contact).where(Contact.created_by_user_id == uid))
            await session.execute(
                delete(ConsentRecord).where(ConsentRecord.recorded_by_user_id == uid)
            )
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_company_api_crud_and_dedup(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="CRM Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    domain = f"acme-{uuid.uuid4().hex[:8]}.com"

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # 1. Create company
            res = await client.post(
                "/contacts/companies",
                json={
                    "name": "Acme Global",
                    "domain": domain,
                    "industry": "SaaS",
                    "lifecycle_stage": "CUSTOMER",
                },
            )
            assert res.status_code == 201, res.text
            data = res.json()
            assert data["name"] == "Acme Global"
            assert data["domain"] == domain
            company_id = data["id"]

            # 2. Duplicate domain is rejected
            dup_res = await client.post(
                "/contacts/companies",
                json={"name": "Acme 2", "domain": domain},
            )
            assert dup_res.status_code == 409

            # 3. Get company
            get_res = await client.get(f"/contacts/companies/{company_id}")
            assert get_res.status_code == 200
            assert get_res.json()["industry"] == "SaaS"

            # 4. List companies
            list_res = await client.get("/contacts/companies")
            assert list_res.status_code == 200
            assert any(c["id"] == company_id for c in list_res.json()["items"])

            # 5. Update company
            update_res = await client.patch(
                f"/contacts/companies/{company_id}",
                json={"industry": "AI & SaaS"},
            )
            assert update_res.status_code == 200
            assert update_res.json()["industry"] == "AI & SaaS"

            # 6. Delete company
            del_res = await client.delete(f"/contacts/companies/{company_id}")
            assert del_res.status_code == 204
    finally:
        await _cleanup_user_artifacts(manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_contact_crm_attributes_and_activities_api(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="CRM Manager 2", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # Create company
            comp_res = await client.post(
                "/contacts/companies",
                json={"name": "Stripe Partner", "domain": f"stripe-{uuid.uuid4().hex[:6]}.com"},
            )
            assert comp_res.status_code == 201
            comp_id = comp_res.json()["id"]

            # Create contact with company_id, job_title, lifecycle_stage
            email = f"lead-{uuid.uuid4().hex[:6]}@example.com"
            contact_res = await client.post(
                "/contacts",
                json={
                    "email": email,
                    "first_name": "Elon",
                    "last_name": "Musk",
                    "phone": "+1555123456",
                    "company_id": comp_id,
                    "job_title": "CEO",
                    "lifecycle_stage": "SQL",
                },
            )
            assert contact_res.status_code == 201, contact_res.text
            contact_data = contact_res.json()
            contact_id = contact_data["id"]
            assert contact_data["company_name"] == "Stripe Partner"
            assert contact_data["job_title"] == "CEO"
            assert contact_data["lifecycle_stage"] == "SQL"

            # Add custom activity
            act_res = await client.post(
                f"/contacts/{contact_id}/activities",
                json={
                    "activity_type": "CALL",
                    "title": "Discovery call completed",
                    "description": "Reviewed pricing structure",
                },
            )
            assert act_res.status_code == 201
            assert act_res.json()["title"] == "Discovery call completed"

            # List activities
            list_act = await client.get(f"/contacts/{contact_id}/activities")
            assert list_act.status_code == 200
            assert len(list_act.json()["items"]) >= 2
    finally:
        await _cleanup_user_artifacts(manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tag_rename_delete_bulk_api(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="CRM Manager 3", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # Create tag
            tag_name = f"tag-{uuid.uuid4().hex[:6]}"
            create_tag_res = await client.post("/contacts/tags", json={"name": tag_name})
            assert create_tag_res.status_code == 201
            tag_id = create_tag_res.json()["id"]

            # Rename tag
            new_name = f"renamed-{uuid.uuid4().hex[:6]}"
            rename_res = await client.patch(f"/contacts/tags/{tag_id}", json={"name": new_name})
            assert rename_res.status_code == 200
            assert rename_res.json()["name"] == new_name

            # Create contact
            c_res = await client.post(
                "/contacts",
                json={"email": f"c-{uuid.uuid4().hex[:6]}@example.com"},
            )
            cid = c_res.json()["id"]

            # Bulk tag
            bulk_res = await client.post(
                "/contacts/bulk-tag",
                json={"contact_ids": [cid], "tag_id": tag_id, "action": "ATTACH"},
            )
            assert bulk_res.status_code == 200
            assert bulk_res.json()["affected"] == 1

            # Delete tag
            del_tag = await client.delete(f"/contacts/tags/{tag_id}")
            assert del_tag.status_code == 204
    finally:
        await _cleanup_user_artifacts(manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_segment_preview_api(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="CRM Manager 4", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            # Seed 2 contacts
            await client.post(
                "/contacts",
                json={
                    "email": f"cust-{uuid.uuid4().hex[:6]}@test.com",
                    "lifecycle_stage": "CUSTOMER",
                },
            )
            await client.post(
                "/contacts",
                json={"email": f"lead-{uuid.uuid4().hex[:6]}@test.com", "lifecycle_stage": "LEAD"},
            )

            preview_res = await client.post(
                "/contacts/segments/preview",
                json={
                    "match_type": "ALL",
                    "rules": [
                        {"field": "lifecycle_stage", "operator": "equals", "value": "CUSTOMER"}
                    ],
                },
            )
            assert preview_res.status_code == 200
            assert preview_res.json()["count"] == 1
    finally:
        await _cleanup_user_artifacts(manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_phone_suppression_api(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="CRM Manager 5", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())
    phone = f"+1800555{uuid.uuid4().hex[:4]}"

    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            supp_res = await client.post(
                "/contacts/suppression/phone",
                json={"phone": phone, "reason": "MANUAL"},
            )
            assert supp_res.status_code == 201
            assert supp_res.json()["phone"] == phone
    finally:
        await _cleanup_user_artifacts(manager_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_crm_multi_tenant_account_isolation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_a = await user_factory(full_name="Tenant A Manager", role_name="Marketing Manager")
    manager_b = await user_factory(full_name="Tenant B Manager", role_name="Marketing Manager")
    transport = ASGITransport(app=create_app())

    try:
        async with (
            AsyncClient(
                transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_a)
            ) as client_a,
            AsyncClient(
                transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_b)
            ) as client_b,
        ):
            # 1. Tenant A creates a company
            res_a = await client_a.post(
                "/contacts/companies",
                json={"name": "Tenant A Corp", "domain": f"t-a-{uuid.uuid4().hex[:6]}.com"},
            )
            assert res_a.status_code == 201
            company_a_id = res_a.json()["id"]

            # 2. Tenant B cannot get, patch, or delete Tenant A's company (404)
            get_b = await client_b.get(f"/contacts/companies/{company_a_id}")
            assert get_b.status_code == 404

            patch_b = await client_b.patch(
                f"/contacts/companies/{company_a_id}",
                json={"name": "Hacked Name"},
            )
            assert patch_b.status_code == 404

            del_b = await client_b.delete(f"/contacts/companies/{company_a_id}")
            assert del_b.status_code == 404

            # 3. Tenant A creates contact & activity
            c_res = await client_a.post(
                "/contacts",
                json={"email": f"isolated-{uuid.uuid4().hex[:6]}@example.com"},
            )
            assert c_res.status_code == 201
            contact_a_id = c_res.json()["id"]

            act_res = await client_a.post(
                f"/contacts/{contact_a_id}/activities",
                json={"activity_type": "NOTE", "title": "Secret Note"},
            )
            assert act_res.status_code == 201

            # 4. Tenant B cannot list Tenant A's contact activities
            act_b = await client_b.get(f"/contacts/{contact_a_id}/activities")
            assert act_b.status_code == 404

            # 5. Tenant B cannot add activities to Tenant A's contact
            act_post_b = await client_b.post(
                f"/contacts/{contact_a_id}/activities",
                json={"activity_type": "NOTE", "title": "Injected Note"},
            )
            assert act_post_b.status_code == 404
    finally:
        await _cleanup_user_artifacts(manager_a, manager_b)


def test_csv_auto_detection() -> None:
    csv_bytes = b"E-mail,First Name,Last Name,Mobile,Company Name,Stage\njohn@example.com,John,Doe,+15551234,Acme Inc,Customer\n"
    res = detect_csv_columns_service(csv_bytes)
    assert "E-mail" in res["headers"]
    assert res["suggested_mapping"]["E-mail"] == "email"
    assert res["suggested_mapping"]["First Name"] == "first_name"
    assert res["suggested_mapping"]["Mobile"] == "phone"
    assert res["suggested_mapping"]["Company Name"] == "company"
    assert res["total_rows_estimate"] == 1
