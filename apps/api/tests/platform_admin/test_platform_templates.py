"""Platform-admin default email template management tests (GRX-EMAIL-016).

Integration-tier: exercises real Postgres and the real create_app() app, same pattern as
test_platform_ai_config.py.
"""

import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from tests.conftest import DEFAULT_TEST_PASSWORD

from growixa_api.app import create_app
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion

TEMPLATE_PAYLOAD = {
    "name": "Platform Welcome",
    "subject": "Welcome to Growixa",
    "body_html": "<p>Hello {{first_name}}</p>",
    "body_text": "Hello {{first_name}}",
}


async def _get_platform_admin_email(admin_id: uuid.UUID) -> str:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PlatformAdmin.email).where(PlatformAdmin.id == admin_id)
        )
        return result.scalar_one()


async def _platform_login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/platform/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}
    )
    assert response.status_code == 200


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(EmailTemplateVersion))
        await session.execute(delete(EmailTemplate))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_owner_can_create_a_platform_default_template(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            response = await client.post("/platform/templates", json=TEMPLATE_PAYLOAD)

        assert response.status_code == 201
        body = response.json()
        assert body["is_platform_default"] is True
        assert body["current_version"]["version_number"] == 1

        async with async_session_factory() as session:
            row = (
                await session.execute(
                    select(EmailTemplate).where(EmailTemplate.id == uuid.UUID(body["id"]))
                )
            ).scalar_one()
        assert row.is_platform_default is True
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_edit_and_retire_a_platform_template(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.admin")
    admin_email = await _get_platform_admin_email(admin_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            create_response = await client.post("/platform/templates", json=TEMPLATE_PAYLOAD)
            template_id = create_response.json()["id"]

            edit_response = await client.post(
                f"/platform/templates/{template_id}/versions",
                json={"subject": "Updated Subject", "body_html": "<p>Updated</p>"},
            )
            assert edit_response.status_code == 200
            assert edit_response.json()["current_version"]["version_number"] == 2
            assert edit_response.json()["current_version"]["subject"] == "Updated Subject"

            list_response = await client.get("/platform/templates")
            assert any(t["id"] == template_id for t in list_response.json())

            retire_response = await client.delete(f"/platform/templates/{template_id}")
            assert retire_response.status_code == 204

            list_after_retire = await client.get("/platform/templates")
            assert all(t["id"] != template_id for t in list_after_retire.json())
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_support_role_is_denied_templates_manage(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Per RBAC.md, only platform.owner/platform.admin get platform.templates.manage --
    platform.support/finance/operations must 403, same higher-trust shape as
    platform.ai.manage/platform.email.manage/platform.validation.manage."""
    admin_id = await platform_admin_factory(role="platform.support")
    admin_email = await _get_platform_admin_email(admin_id)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        create_response = await client.post("/platform/templates", json=TEMPLATE_PAYLOAD)
        list_response = await client.get("/platform/templates")

    assert create_response.status_code == 403
    assert list_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_editing_a_platform_template_appends_a_version_without_mutating_the_old_one(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _platform_login(client, admin_email)
            create_response = await client.post("/platform/templates", json=TEMPLATE_PAYLOAD)
            template_id = create_response.json()["id"]

            await client.post(
                f"/platform/templates/{template_id}/versions",
                json={"subject": "v2", "body_html": "<p>v2</p>"},
            )

        async with async_session_factory() as session:
            versions = (
                (
                    await session.execute(
                        select(EmailTemplateVersion).where(
                            EmailTemplateVersion.template_id == uuid.UUID(template_id)
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert {v.version_number for v in versions} == {1, 2}
        original = next(v for v in versions if v.version_number == 1)
        assert original.subject == "Welcome to Growixa"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_editing_or_retiring_nonexistent_template_returns_404(
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await platform_admin_factory(role="platform.owner")
    admin_email = await _get_platform_admin_email(admin_id)
    fake_id = uuid.uuid4()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _platform_login(client, admin_email)
        edit_response = await client.post(
            f"/platform/templates/{fake_id}/versions",
            json={"subject": "x", "body_html": "<p>x</p>"},
        )
        retire_response = await client.delete(f"/platform/templates/{fake_id}")

    assert edit_response.status_code == 404
    assert retire_response.status_code == 404
