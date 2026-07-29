"""User list/status/role-change integration tests (GRX-USER-002).

Integration-tier: exercises real Postgres and the real create_app() app, using the shared
user_factory fixture (conftest.py).
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.models import RefreshToken
from growixa_api.auth.tokens import generate_token as generate_refresh_token
from growixa_api.auth.tokens import hash_token as hash_refresh_token
from growixa_api.auth.tokens import refresh_token_expiry
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.users.models import User, UserRole


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup(*user_ids: uuid.UUID) -> None:
    async with async_session_factory() as session:
        for user_id in user_ids:
            await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
            await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user_id))
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "user", AuditLog.entity_id == user_id
                )
            )
            # user_roles.assigned_by_user_id has no ON DELETE CASCADE — a role change in
            # the test leaves a row referencing the admin as the assigner, which would
            # otherwise block user_factory's teardown from deleting that admin.
            await session.execute(delete(UserRole).where(UserRole.assigned_by_user_id == user_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_list_users_with_roles_and_status(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Listing Admin", role_name="Admin")
    viewer_id = await user_factory(full_name="Listed Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.get("/users")

    assert response.status_code == 200
    body = {row["id"]: row for row in response.json()}
    assert str(admin_id) in body
    assert str(viewer_id) in body
    assert body[str(admin_id)]["roles"] == ["Admin"]
    assert body[str(viewer_id)]["roles"] == ["Viewer"]
    assert body[str(viewer_id)]["status"] == "ACTIVE"

    await _cleanup(admin_id, viewer_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_admin_cannot_list_users(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Plain Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.get("/users")

    assert response.status_code == 403

    await _cleanup(viewer_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_disable_a_user_which_revokes_their_sessions(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Disabling Admin", role_name="Admin")
    target_id = await user_factory(full_name="Target User", role_name="Viewer")

    # give the target user an active session to prove disabling revokes it
    raw_refresh = generate_refresh_token()
    async with async_session_factory() as session:
        session.add(
            RefreshToken(
                user_id=target_id,
                token_hash=hash_refresh_token(raw_refresh),
                expires_at=refresh_token_expiry(),
            )
        )
        await session.commit()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.patch(f"/users/{target_id}/status", json={"status": "DISABLED"})

    assert response.status_code == 200
    assert response.json()["status"] == "DISABLED"

    async with async_session_factory() as session:
        token_result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == target_id)
        )
        tokens = token_result.scalars().all()
        user = await session.get(User, target_id)
        audit_result = await session.execute(
            select(AuditLog).where(AuditLog.action == "session.revoked")
        )
        revoked_events = [e for e in audit_result.scalars().all() if e.entity_id == target_id]

    assert all(token.revoked_at is not None for token in tokens)
    assert user is not None
    assert user.status == "DISABLED"
    assert len(revoked_events) == 1
    assert revoked_events[0].event_metadata["reason"] == "account_disabled"

    await _cleanup(admin_id, target_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_disable_their_own_account(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Self Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.patch(f"/users/{admin_id}/status", json={"status": "DISABLED"})

    assert response.status_code == 400

    async with async_session_factory() as session:
        user = await session.get(User, admin_id)
    assert user is not None
    assert user.status == "ACTIVE"

    await _cleanup(admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_disabling_an_unknown_user_is_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Disabling Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.patch(f"/users/{uuid.uuid4()}/status", json={"status": "DISABLED"})

    assert response.status_code == 404

    await _cleanup(admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_change_a_users_role(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Role Admin", role_name="Admin")
    target_id = await user_factory(full_name="Role Target", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.patch(f"/users/{target_id}/role", json={"role_name": "Analyst"})

    assert response.status_code == 200
    assert response.json()["roles"] == ["Analyst"]

    async with async_session_factory() as session:
        role_result = await session.execute(select(UserRole).where(UserRole.user_id == target_id))
        user_roles = role_result.scalars().all()
        audit_result = await session.execute(
            select(AuditLog).where(AuditLog.action == "role.changed")
        )
        events = [e for e in audit_result.scalars().all() if e.entity_id == target_id]

    assert len(user_roles) == 1
    assert len(events) == 1
    assert events[0].actor_user_id == admin_id
    assert events[0].event_metadata["old_roles"] == ["Viewer"]
    assert events[0].event_metadata["new_role"] == "Analyst"

    await _cleanup(admin_id, target_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_changing_to_an_unknown_role_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Role Admin", role_name="Admin")
    target_id = await user_factory(full_name="Role Target", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.patch(
            f"/users/{target_id}/role", json={"role_name": "Not A Real Role"}
        )

    assert response.status_code == 400

    await _cleanup(admin_id, target_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_admin_cannot_change_role(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Plain Viewer", role_name="Viewer")
    target_id = await user_factory(full_name="Role Target", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.patch(f"/users/{target_id}/role", json={"role_name": "Analyst"})

    assert response.status_code == 403

    await _cleanup(viewer_id, target_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_list_roles(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Roles Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.get("/roles")

    assert response.status_code == 200
    names = {role["name"] for role in response.json()}
    assert {
        "Super Admin",
        "Admin",
        "Marketing Manager",
        "Content Creator",
        "Analyst",
        "Viewer",
    } <= names

    await _cleanup(admin_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_admin_cannot_list_roles(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Plain Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.get("/roles")

    assert response.status_code == 403

    await _cleanup(viewer_id)
