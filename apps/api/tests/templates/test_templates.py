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
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.campaigns.models import Campaign
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
from growixa_api.templates.schemas import EmailTemplateIn
from growixa_api.templates.services import create_platform_template, retire_platform_template

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
        await session.execute(delete(Campaign).where(Campaign.name == "Uses the template"))
        connection_ids = (
            (
                await session.execute(
                    select(SenderIdentity.email_provider_connection_id).where(
                        SenderIdentity.from_email == "hello@growixa.local"
                    )
                )
            )
            .scalars()
            .all()
        )
        await session.execute(
            delete(SenderIdentity).where(SenderIdentity.from_email == "hello@growixa.local")
        )
        await session.execute(
            delete(EmailProviderConnection).where(EmailProviderConnection.id.in_(connection_ids))
        )
        await session.execute(delete(EmailTemplateVersion))
        await session.execute(delete(EmailTemplate))
        await session.commit()


async def _create_platform_template(
    *,
    name: str = "Platform Welcome Default",
    subject: str = "Welcome to Growixa",
    body_html: str = "<p>Hello {{first_name}}</p>",
) -> uuid.UUID:
    """Direct service-layer creation (GRX-EMAIL-016) -- bypasses the platform-admin HTTP
    API/auth entirely, same pattern as this file's other fixture setup
    (_create_campaign_referencing_template), since these tests exercise the
    customer-facing routes, not the platform-admin ones (covered separately in
    tests/platform_admin/test_platform_templates.py)."""
    async with async_session_factory() as session:
        template, _version = await create_platform_template(
            session, EmailTemplateIn(name=name, subject=subject, body_html=body_html)
        )
        await session.commit()
        return template.id


async def _create_campaign_referencing_template(
    account_id: uuid.UUID, template_id: uuid.UUID, actor_id: uuid.UUID
) -> None:
    async with async_session_factory() as session:
        connection = EmailProviderConnection(
            account_id=account_id,
            name="Template Postmark",
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted=encrypt_secret("fake-smtp-password"),
        )
        session.add(connection)
        await session.flush()
        identity = SenderIdentity(
            account_id=account_id,
            email_provider_connection_id=connection.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.flush()
        campaign = Campaign(
            account_id=account_id,
            name="Uses the template",
            subject="Hi",
            body_html="<p>Hi</p>",
            template_id=template_id,
            sender_identity_id=identity.id,
            recipient_type="ALL_CONTACTS",
            created_by_user_id=actor_id,
        )
        session.add(campaign)
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
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=account_id
    )
    analyst_id = await user_factory(
        full_name="Test Analyst", role_name="Analyst", account_id=account_id
    )
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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_delete_an_unused_template(
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

            delete_response = await client.delete(f"/templates/{template_id}")
            list_response = await client.get("/templates")

        assert delete_response.status_code == 204
        assert all(t["id"] != template_id for t in list_response.json())
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deleting_an_unknown_template_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.delete(f"/templates/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_view_only_role_cannot_delete(
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
            delete_attempt = await analyst_client.delete(f"/templates/{template_id}")

        assert delete_attempt.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deleting_a_template_referenced_by_a_campaign_returns_409(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """campaigns.template_id has no ON DELETE behavior — a campaign copies a template's
    content at creation time rather than depending on it, but the FK still exists to
    preserve the "created from" link, so deleting a referenced template must be blocked
    with a clean error, not a raw 500."""
    account_id = await account_factory()
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=account_id
    )
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            create_response = await client.post("/templates", json=TEMPLATE_PAYLOAD)
            template_id = create_response.json()["id"]

            await _create_campaign_referencing_template(
                account_id, uuid.UUID(template_id), manager_id
            )

            delete_response = await client.delete(f"/templates/{template_id}")
            list_response = await client.get("/templates")

        assert delete_response.status_code == 409
        assert any(t["id"] == template_id for t in list_response.json())
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_template_with_invalid_token_returns_422(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            invalid_payload = {
                "name": "Invalid Template",
                "subject": "Hello {{typo_tag}}",
                "body_html": "<p>Content</p>",
            }
            res = await client.post("/templates", json=invalid_payload)
            assert res.status_code == 422
            detail = res.json()["detail"]
            assert "Invalid personalization token" in detail
            assert "typo_tag" in detail
            assert "Available tokens:" in detail
    finally:
        await _cleanup()


# --- Platform-published default templates (GRX-EMAIL-016) -----------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_platform_defaults_route_lists_platform_templates_not_account_owned_ones(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    try:
        platform_template_id = await _create_platform_template()
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            own_create = await client.post("/templates", json=TEMPLATE_PAYLOAD)
            own_template_id = own_create.json()["id"]

            defaults_response = await client.get("/templates/platform-defaults")
            own_response = await client.get("/templates")

        assert defaults_response.status_code == 200
        default_ids = {t["id"] for t in defaults_response.json()}
        assert platform_template_id in {uuid.UUID(i) for i in default_ids}
        assert own_template_id not in default_ids
        assert all(t["is_platform_default"] for t in defaults_response.json())

        assert own_response.status_code == 200
        own_ids = {t["id"] for t in own_response.json()}
        assert own_template_id in own_ids
        assert str(platform_template_id) not in own_ids
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_clone_creates_independent_copy_unaffected_by_later_platform_edits(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    try:
        platform_template_id = await _create_platform_template(
            subject="Original Subject", body_html="<p>Original body</p>"
        )
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            clone_response = await client.post(f"/templates/{platform_template_id}/clone")
            assert clone_response.status_code == 201
            clone = clone_response.json()
            assert clone["is_platform_default"] is False
            assert clone["current_version"]["subject"] == "Original Subject"
            clone_id = clone["id"]

            # Retiring the platform original afterwards (GRX-EMAIL-016's own service, not
            # the customer-facing API -- platform admins never authenticate as a customer)
            async with async_session_factory() as session:
                await retire_platform_template(session, platform_template_id)
                await session.commit()

            # The clone is a fully independent row -- retiring the original must not
            # affect it at all.
            get_clone_response = await client.get(f"/templates/{clone_id}")
        assert get_clone_response.status_code == 200
        assert get_clone_response.json()["current_version"]["subject"] == "Original Subject"
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_clone_requires_manage_permission(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")
    cookies = _access_token_cookie(analyst_id)
    try:
        platform_template_id = await _create_platform_template()
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(f"/templates/{platform_template_id}/clone")
        assert response.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_account_cannot_read_or_mutate_a_platform_template_via_account_scoped_routes(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Account-isolation regression (GRX-EMAIL-016): the normal account-scoped
    /templates/{id} routes filter by account_id, and a platform template's account_id is
    the reserved platform system account, never the caller's -- so every one of these
    must 404, not silently succeed or leak content."""
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    try:
        platform_template_id = await _create_platform_template()
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            get_response = await client.get(f"/templates/{platform_template_id}")
            versions_response = await client.get(f"/templates/{platform_template_id}/versions")
            edit_response = await client.post(
                f"/templates/{platform_template_id}/versions",
                json={"subject": "Hijacked", "body_html": "<p>x</p>"},
            )
            delete_response = await client.delete(f"/templates/{platform_template_id}")

        assert get_response.status_code == 404
        assert versions_response.status_code == 404
        assert edit_response.status_code == 404
        assert delete_response.status_code == 404
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_clone_of_nonexistent_template_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.post(f"/templates/{uuid.uuid4()}/clone")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_clone_of_a_regular_account_owned_template_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """The clone endpoint only ever clones a platform default -- a regular
    account-owned template_id (even the account's own) is never a valid target, since the
    "Use this template" action only exists for platform-published templates."""
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            create_response = await client.post("/templates", json=TEMPLATE_PAYLOAD)
            own_template_id = create_response.json()["id"]
            clone_response = await client.post(f"/templates/{own_template_id}/clone")
        assert clone_response.status_code == 404
    finally:
        await _cleanup()
