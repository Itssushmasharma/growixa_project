"""Email template + versioning integration tests (GRX-EMAIL-002).

Integration-tier: exercises real Postgres and the real create_app() app. Rows created by a
test are cleaned up by that test (via _cleanup), matching the established pattern (e.g.
test_integrations.py) rather than an autouse fixture, since templates reference users.id
without ON DELETE CASCADE.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion

TEMPLATE_PAYLOAD = {
    "name": "Welcome Email",
    "subject": "Welcome to Growixa",
    "body_html": "<p>Hello {{first_name}}</p>",
    "body_text": "Hello {{first_name}}",
}


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(EmailTemplateVersion))
        await session.execute(delete(EmailTemplate))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_a_template(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post("/templates", json=TEMPLATE_PAYLOAD)

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Welcome Email"
        assert body["current_version"]["version_number"] == 1
        assert body["current_version"]["subject"] == "Welcome to Growixa"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_editing_a_template_creates_a_new_version_without_mutating_the_old_one(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            create_response = await client.post("/templates", json=TEMPLATE_PAYLOAD)
            template_id = create_response.json()["id"]

            edit_response = await client.post(
                f"/templates/{template_id}/versions",
                json={
                    "subject": "Welcome to Growixa v2",
                    "body_html": "<p>Hi {{first_name}}</p>",
                },
            )
            assert edit_response.status_code == 200
            edited_body = edit_response.json()
            assert edited_body["current_version"]["version_number"] == 2
            assert edited_body["current_version"]["subject"] == "Welcome to Growixa v2"

            versions_response = await client.get(f"/templates/{template_id}/versions")

        assert versions_response.status_code == 200
        versions = versions_response.json()
        assert len(versions) == 2
        assert {v["version_number"] for v in versions} == {1, 2}
        original = next(v for v in versions if v["version_number"] == 1)
        assert original["subject"] == "Welcome to Growixa"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_view_only_role_can_read_but_not_create_or_edit(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(manager_id),
        ) as manager_client:
            create_response = await manager_client.post("/templates", json=TEMPLATE_PAYLOAD)
            template_id = create_response.json()["id"]

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(analyst_id),
        ) as analyst_client:
            list_response = await analyst_client.get("/templates")
            get_response = await analyst_client.get(f"/templates/{template_id}")
            create_attempt = await analyst_client.post("/templates", json=TEMPLATE_PAYLOAD)
            edit_attempt = await analyst_client.post(
                f"/templates/{template_id}/versions",
                json={"subject": "Hijacked", "body_html": "<p>x</p>"},
            )

        assert list_response.status_code == 200
        assert get_response.status_code == 200
        assert create_attempt.status_code == 403
        assert edit_attempt.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_role_gets_403_on_read(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")
    cookies = _access_token_cookie(viewer_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.get("/templates")

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_response = await client.get("/templates")
        post_response = await client.post("/templates", json=TEMPLATE_PAYLOAD)

    assert get_response.status_code == 401
    assert post_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_and_edit_unknown_template_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        get_response = await client.get(f"/templates/{unknown_id}")
        versions_response = await client.get(f"/templates/{unknown_id}/versions")
        edit_response = await client.post(
            f"/templates/{unknown_id}/versions",
            json={"subject": "x", "body_html": "<p>x</p>"},
        )

    assert get_response.status_code == 404
    assert versions_response.status_code == 404
    assert edit_response.status_code == 404
