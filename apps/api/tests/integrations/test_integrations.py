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
    "name": "Postmark Production",
    "provider": "POSTMARK",
    "smtp_host": "smtp.postmarkapp.com",
    "smtp_port": 587,
    "smtp_username": "postmark-server-token",
    "smtp_password": "super-secret-smtp-password",
}

CUSTOM_SMTP_PAYLOAD = {
    "name": "Custom SMTP Relay",
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
            assert body["name"] == CONNECTION_PAYLOAD["name"]

            get_response = await client.get("/integrations/email-providers")

        assert get_response.status_code == 200
        connections = get_response.json()
        assert len(connections) == 1
        assert connections[0]["smtp_host"] == "smtp.postmarkapp.com"
        assert connections[0]["name"] == CONNECTION_PAYLOAD["name"]

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
async def test_admin_cannot_access_integrations_endpoints(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    cookies = _access_token_cookie(admin_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        assert (await client.get("/integrations/email-providers")).status_code == 403
        assert (
            await client.post("/integrations/email-provider", json=CONNECTION_PAYLOAD)
        ).status_code == 403
        assert (await client.get("/integrations/sender-identities")).status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postmark_single_active_connection_per_account(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            first_response = await client.post(
                "/integrations/email-provider", json=CONNECTION_PAYLOAD
            )
            assert first_response.status_code == 201
            first_id = uuid.UUID(first_response.json()["id"])

            second_payload = {
                **CONNECTION_PAYLOAD,
                "name": "Second Postmark",
                "smtp_username": "second-token",
            }
            second_response = await client.post("/integrations/email-provider", json=second_payload)
            assert second_response.status_code == 201
            second_id = uuid.UUID(second_response.json()["id"])

        async with async_session_factory() as session:
            first_row = await session.get(EmailProviderConnection, first_id)
            second_row = await session.get(EmailProviderConnection, second_id)
            assert first_row is not None and not first_row.is_active
            assert second_row is not None and second_row.is_active
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_custom_smtp_connections_allowed_with_distinct_names(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """DEC-GRX-035 Point 1: Multiple CUSTOM_SMTP connections can be active on one account."""
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            conn1_resp = await client.post(
                "/integrations/email-provider",
                json={
                    **CUSTOM_SMTP_PAYLOAD,
                    "name": "Transactional Relay",
                    "smtp_host": "smtp1.example.com",
                },
            )
            assert conn1_resp.status_code == 201
            conn1_id = uuid.UUID(conn1_resp.json()["id"])

            conn2_resp = await client.post(
                "/integrations/email-provider",
                json={
                    **CUSTOM_SMTP_PAYLOAD,
                    "name": "Marketing Relay",
                    "smtp_host": "smtp2.example.com",
                },
            )
            assert conn2_resp.status_code == 201
            conn2_id = uuid.UUID(conn2_resp.json()["id"])

            get_resp = await client.get("/integrations/email-providers")
            assert get_resp.status_code == 200
            connections = get_resp.json()
            active_smtp = [
                c for c in connections if c["provider"] == "CUSTOM_SMTP" and c["is_active"]
            ]
            assert len(active_smtp) == 2

        async with async_session_factory() as session:
            row1 = await session.get(EmailProviderConnection, conn1_id)
            row2 = await session.get(EmailProviderConnection, conn2_id)
            assert row1 is not None and row1.is_active
            assert row2 is not None and row2.is_active
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sender_identity_lifecycle_and_verification_status(
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

            create_identity_response = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": connection_id,
                    "from_email": "hello@growixa.local",
                    "from_name": "Growixa",
                    "reply_to_email": "support@growixa.local",
                },
            )
            assert create_identity_response.status_code == 201
            created = create_identity_response.json()
            assert created["verification_status"] == "PENDING"
            assert created["from_email"] == "hello@growixa.local"
            identity_id = created["id"]

            list_response = await client.get("/integrations/sender-identities")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 1

            status_response = await client.patch(
                f"/integrations/sender-identities/{identity_id}/status",
                json={"verification_status": "VERIFIED"},
            )
            assert status_response.status_code == 200
            assert status_response.json()["verification_status"] == "VERIFIED"
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_guarded_delete_email_provider_connection(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """DEC-GRX-035 Point 7: Deleting a connection is blocked while any sender identity
    references it."""
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            conn_resp = await client.post(
                "/integrations/email-provider",
                json={**CUSTOM_SMTP_PAYLOAD, "name": "Guarded Relay"},
            )
            conn_id = conn_resp.json()["id"]

            # Create sender identity referencing it
            await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": conn_id,
                    "from_email": "bound@growixa.local",
                    "from_name": "Bound Sender",
                },
            )

            # Try deleting connection -> 409 Conflict naming the blocking sender identity
            del_resp = await client.delete(f"/integrations/email-providers/{conn_id}")
            assert del_resp.status_code == 409
            assert "bound@growixa.local" in del_resp.json()["detail"]

            # Create second unreferenced connection and delete it -> 204 No Content
            unref_conn_resp = await client.post(
                "/integrations/email-provider",
                json={**CUSTOM_SMTP_PAYLOAD, "name": "Unreferenced Relay"},
            )
            unref_conn_id = unref_conn_resp.json()["id"]

            del_unref_resp = await client.delete(f"/integrations/email-providers/{unref_conn_id}")
            assert del_unref_resp.status_code == 204

            # Verify it is removed from list_email_provider_connections
            list_resp = await client.get("/integrations/email-providers")
            assert not any(c["id"] == unref_conn_id for c in list_resp.json())
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_replacing_invalid_connection_id_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Proves supplying a non-existent or inactive replacing_connection_id returns 404."""
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            resp = await client.post(
                "/integrations/email-provider",
                json={
                    **CUSTOM_SMTP_PAYLOAD,
                    "name": "Orphaned Replacement",
                    "replacing_connection_id": str(uuid.uuid4()),
                },
            )
            assert resp.status_code == 404
            assert "not found" in resp.json()["detail"].lower()
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_replacing_connection_narrows_reassignment_regression(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """DEC-GRX-035 Point 8 (CRITICAL REGRESSION TEST):
    Replacing connection A only reassigns identities referencing connection A.
    Identities referencing connection B remain bound to connection B!
    """
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            # 1. Create connection A (Transactional) and connection B (Marketing)
            conn_a = await client.post(
                "/integrations/email-provider",
                json={
                    **CUSTOM_SMTP_PAYLOAD,
                    "name": "Transactional Relay",
                    "smtp_host": "transac.smtp.com",
                },
            )
            conn_a_id = conn_a.json()["id"]

            conn_b = await client.post(
                "/integrations/email-provider",
                json={
                    **CUSTOM_SMTP_PAYLOAD,
                    "name": "Marketing Relay",
                    "smtp_host": "mktg.smtp.com",
                },
            )
            conn_b_id = conn_b.json()["id"]

            # 2. Bind identity 1 -> Connection A, identity 2 -> Connection B
            id1_resp = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": conn_a_id,
                    "from_email": "transac@growixa.local",
                    "from_name": "Transactional Sender",
                },
            )
            id1 = id1_resp.json()["id"]

            id2_resp = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": conn_b_id,
                    "from_email": "marketing@growixa.local",
                    "from_name": "Marketing Sender",
                },
            )
            id2 = id2_resp.json()["id"]

            # 3. Replace connection A with a new updated connection A'
            conn_a_prime = await client.post(
                "/integrations/email-provider",
                json={
                    **CUSTOM_SMTP_PAYLOAD,
                    "name": "Transactional Relay V2",
                    "smtp_host": "transac2.smtp.com",
                    "replacing_connection_id": conn_a_id,
                },
            )
            conn_a_prime_id = conn_a_prime.json()["id"]

            # 4. Assert: identity 1 is reassigned to A', but identity 2 STILL points to B!
            list_res = await client.get("/integrations/sender-identities")
            identities = {i["id"]: i["email_provider_connection_id"] for i in list_res.json()}

            assert identities[id1] == conn_a_prime_id
            assert identities[id2] == conn_b_id  # Unchanged!
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_sender_identity_connection(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Tests updating a sender identity's connection to another connection."""
    super_admin_id = await user_factory(full_name="Test Super Admin", role_name="Super Admin")
    try:
        cookies = _access_token_cookie(super_admin_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            conn1 = await client.post(
                "/integrations/email-provider",
                json={**CUSTOM_SMTP_PAYLOAD, "name": "Relay 1"},
            )
            conn1_id = conn1.json()["id"]

            conn2 = await client.post(
                "/integrations/email-provider",
                json={**CUSTOM_SMTP_PAYLOAD, "name": "Relay 2"},
            )
            conn2_id = conn2.json()["id"]

            id_resp = await client.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": conn1_id,
                    "from_email": "moveme@growixa.local",
                    "from_name": "Moveable Sender",
                },
            )
            identity_id = id_resp.json()["id"]

            patch_resp = await client.patch(
                f"/integrations/sender-identities/{identity_id}",
                json={"email_provider_connection_id": conn2_id},
            )
            assert patch_resp.status_code == 200
            assert patch_resp.json()["email_provider_connection_id"] == conn2_id
    finally:
        await _cleanup(super_admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_account_isolation_on_email_providers(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """Proves account A cannot read, delete, or bind identities to account B's connections."""
    super_admin_a = await user_factory(full_name="Super Admin A", role_name="Super Admin")
    super_admin_b = await user_factory(full_name="Super Admin B", role_name="Super Admin")
    try:
        cookies_a = _access_token_cookie(super_admin_a)
        cookies_b = _access_token_cookie(super_admin_b)
        transport = ASGITransport(app=create_app())

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies_a
        ) as client_a:
            conn_a_resp = await client_a.post(
                "/integrations/email-provider",
                json={**CUSTOM_SMTP_PAYLOAD, "name": "Account A Relay"},
            )
            conn_a_id = conn_a_resp.json()["id"]

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies_b
        ) as client_b:
            # Account B lists connections -> does not see Account A's connection
            list_b = await client_b.get("/integrations/email-providers")
            assert not any(c["id"] == conn_a_id for c in list_b.json())

            # Account B attempts to delete Account A's connection -> 404
            del_resp = await client_b.delete(f"/integrations/email-providers/{conn_a_id}")
            assert del_resp.status_code == 404

            # Account B attempts to bind identity to Account A's connection -> 404
            bind_resp = await client_b.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": conn_a_id,
                    "from_email": "intruder@growixa.local",
                    "from_name": "Intruder",
                },
            )
            assert bind_resp.status_code == 404
    finally:
        await _cleanup(super_admin_a)
        await _cleanup(super_admin_b)
