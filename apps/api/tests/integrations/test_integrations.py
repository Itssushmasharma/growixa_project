"""Email provider connection + sender identity integration tests (GRX-EMAIL-001).

Integration-tier: exercises real Postgres and the real create_app() app. `integrations.manage`
is the project's first Admin-excluded permission (Super Admin only, per RBAC.md's Slice 3
permission codes), so the Admin-gets-403 test matters more than usual here.

Rows created by a test are cleaned up by that test (via _cleanup), not an autouse fixture:
email_provider_connections/sender_identities reference users.id without ON DELETE CASCADE, so
cleanup must run before user_factory's own teardown deletes the referencing user (see
conftest.py's user_factory docstring).
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.auth.encryption import decrypt_secret
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity

CONNECTION_PAYLOAD = {
    "provider": "POSTMARK",
    "smtp_host": "smtp.postmarkapp.com",
    "smtp_port": 587,
    "smtp_username": "postmark-server-token",
    "smtp_password": "super-secret-smtp-password",
}

CUSTOM_SMTP_PAYLOAD = {
    "provider": "CUSTOM_SMTP",
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_username": "custom-smtp-username",
    "smtp_password": "custom-smtp-password",
}


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup(created_by_user_id: uuid.UUID) -> None:
    """Scoped by created_by_user_id (the actor each test's own user_factory-created user
    passes when calling the create endpoints) rather than by payload values, since
    individual tests vary smtp_username per call (e.g. a "second-token" override) — an
    actor-scoped delete catches every row a test created regardless of payload shape."""
    async with async_session_factory() as session:
        await session.execute(
            delete(SenderIdentity).where(SenderIdentity.created_by_user_id == created_by_user_id)
        )
        await session.execute(
            delete(EmailProviderConnection).where(
                EmailProviderConnection.created_by_user_id == created_by_user_id
            )
        )
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_super_admin_can_create_connection_and_password_is_encrypted(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            post_response = await client.post(
                "/integrations/email-provider", json=CONNECTION_PAYLOAD
            )
            assert post_response.status_code == 201
            body = post_response.json()
            assert "smtp_password" not in body
            assert "smtp_password_encrypted" not in body

            get_response = await client.get("/integrations/email-providers")

        assert get_response.status_code == 200
        connections = get_response.json()
        assert len(connections) == 1
        assert connections[0]["smtp_host"] == "smtp.postmarkapp.com"

        async with async_session_factory() as session:
            row = await session.get(EmailProviderConnection, uuid.UUID(body["id"]))
            assert row is not None
            assert row.smtp_password_encrypted != CONNECTION_PAYLOAD["smtp_password"]
            assert (
                decrypt_secret(row.smtp_password_encrypted) == CONNECTION_PAYLOAD["smtp_password"]
            )
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_creating_a_new_connection_deactivates_the_previous_one_for_that_provider(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            await client.post("/integrations/email-provider", json=CONNECTION_PAYLOAD)
            second_payload = {**CONNECTION_PAYLOAD, "smtp_username": "second-token"}
            second_response = await client.post("/integrations/email-provider", json=second_payload)

            get_response = await client.get("/integrations/email-providers")

        assert second_response.status_code == 201
        connections = get_response.json()
        postmark_connections = [c for c in connections if c["provider"] == "POSTMARK"]
        assert len(postmark_connections) == 2
        active = [c for c in postmark_connections if c["is_active"]]
        assert len(active) == 1
        assert active[0]["smtp_username"] == "second-token"
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_connecting_a_different_provider_leaves_the_other_active(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """GRX-EMAIL-011: "singleton by convention" became "one active connection per
    provider" — connecting Custom SMTP must not touch an already-active Postmark row,
    and vice versa."""
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            await client.post("/integrations/email-provider", json=CONNECTION_PAYLOAD)
            custom_smtp_response = await client.post(
                "/integrations/email-provider", json=CUSTOM_SMTP_PAYLOAD
            )
            get_response = await client.get("/integrations/email-providers")

        assert custom_smtp_response.status_code == 201
        connections = get_response.json()
        assert len(connections) == 2
        assert all(c["is_active"] for c in connections)
        providers = {c["provider"] for c in connections}
        assert providers == {"POSTMARK", "CUSTOM_SMTP"}
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_provider_value_returns_422(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(
                "/integrations/email-provider",
                json={**CONNECTION_PAYLOAD, "provider": "SENDGRID"},
            )

        assert response.status_code == 422
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_403_on_integrations_manage_routes(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    cookies = _access_token_cookie(admin_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        get_response = await client.get("/integrations/email-providers")
        post_response = await client.post("/integrations/email-provider", json=CONNECTION_PAYLOAD)

    assert get_response.status_code == 403
    assert post_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_response = await client.get("/integrations/email-providers")
        post_response = await client.post("/integrations/email-provider", json=CONNECTION_PAYLOAD)

    assert get_response.status_code == 401
    assert post_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_super_admin_can_create_and_list_sender_identities(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            connection_response = await client.post(
                "/integrations/email-provider", json=CONNECTION_PAYLOAD
            )
            connection_id = connection_response.json()["id"]

            identity_response = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": connection_id,
                    "from_email": "hello@growixa.local",
                    "from_name": "Growixa",
                },
            )
            assert identity_response.status_code == 201
            identity_body = identity_response.json()
            assert identity_body["verification_status"] == "PENDING"

            list_response = await client.get("/integrations/sender-identities")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 1

            status_response = await client.patch(
                f"/integrations/sender-identities/{identity_body['id']}/status",
                json={"verification_status": "VERIFIED"},
            )

        assert status_response.status_code == 200
        assert status_response.json()["verification_status"] == "VERIFIED"
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sender_identity_rejects_unknown_connection(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": str(uuid.uuid4()),
                    "from_email": "hello@growixa.local",
                    "from_name": "Growixa",
                },
            )

        assert response.status_code == 404
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sender_identity_status_update_rejects_invalid_status(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            connection_response = await client.post(
                "/integrations/email-provider", json=CONNECTION_PAYLOAD
            )
            connection_id = connection_response.json()["id"]
            identity_response = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": connection_id,
                    "from_email": "hello@growixa.local",
                    "from_name": "Growixa",
                },
            )
            identity_id = identity_response.json()["id"]

            response = await client.patch(
                f"/integrations/sender-identities/{identity_id}/status",
                json={"verification_status": "NOT_A_REAL_STATUS"},
            )

        assert response.status_code == 400
    finally:
        await _cleanup(super_admin_id)
