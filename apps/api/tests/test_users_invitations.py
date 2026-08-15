"""User invitation create/accept integration tests (GRX-USER-001).

Integration-tier: exercises real Postgres and the real create_app() app, using the shared
user_factory fixture (conftest.py) for the inviting Admin.
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
from growixa_api.db import async_session_factory
from growixa_api.users.models import User, UserInvitation, UserRole
from tests.conftest import grant_unlimited_plan


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_invitation(email: str) -> None:
    async with async_session_factory() as session:
        invitation_result = await session.execute(
            select(UserInvitation).where(UserInvitation.email == email)
        )
        invitations = invitation_result.scalars().all()
        for invitation in invitations:
            await session.execute(delete(AuditLog).where(AuditLog.entity_id == invitation.id))
        await session.execute(delete(UserInvitation).where(UserInvitation.email == email))

        user_result = await session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        if user is not None:
            await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == user.id))
            await session.execute(delete(UserRole).where(UserRole.user_id == user.id))
            await session.execute(delete(User).where(User.id == user.id))

        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_can_invite_and_invitee_can_accept(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Inviting Admin", role_name="Admin")
    async with async_session_factory() as session:
        admin_account_id = (
            await session.execute(select(User.account_id).where(User.id == admin_id))
        ).scalar_one()
    await grant_unlimited_plan(admin_account_id)
    invitee_email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as admin_client:
        invite_response = await admin_client.post(
            "/users/invitations", json={"email": invitee_email, "role_name": "Viewer"}
        )

    assert invite_response.status_code == 201
    invite_body = invite_response.json()
    assert invite_body["email"] == invitee_email
    raw_token = invite_body["token"]
    assert raw_token

    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        accept_response = await anon_client.post(
            "/users/invitations/accept",
            json={"token": raw_token, "password": "Invitee-Pass-123!", "full_name": "New Viewer"},
        )

    assert accept_response.status_code == 200
    accept_body = accept_response.json()
    assert accept_body["email"] == invitee_email
    assert accept_body["full_name"] == "New Viewer"
    new_user_id = uuid.UUID(accept_body["id"])

    async with async_session_factory() as session:
        role_result = await session.execute(select(UserRole).where(UserRole.user_id == new_user_id))
        user_roles = role_result.scalars().all()
        invitation_result = await session.execute(
            select(UserInvitation).where(UserInvitation.email == invitee_email)
        )
        invitation = invitation_result.scalar_one()
        audit_result = await session.execute(
            select(AuditLog).where(AuditLog.action == "invitation.accepted")
        )
        events = [e for e in audit_result.scalars().all() if e.entity_id == invitation.id]

    assert len(user_roles) == 1
    assert invitation.accepted_at is not None
    assert len(events) == 1
    assert events[0].actor_user_id == new_user_id

    await _cleanup_invitation(invitee_email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_admin_cannot_invite(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Plain Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.post(
            "/users/invitations",
            json={"email": f"{uuid.uuid4()}@example.com", "role_name": "Viewer"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invite_unknown_role_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Inviting Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/users/invitations",
            json={"email": f"{uuid.uuid4()}@example.com", "role_name": "Not A Real Role"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invite_existing_user_email_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Inviting Admin", role_name="Admin")
    existing_email = f"{uuid.uuid4()}@example.com"
    await user_factory(full_name="Existing User", email=existing_email)

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/users/invitations", json={"email": existing_email, "role_name": "Viewer"}
        )

    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_accepting_with_invalid_token_is_rejected() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/users/invitations/accept",
            json={"token": "not-a-real-token", "password": "x", "full_name": "Nobody"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_accepting_an_already_accepted_invitation_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Inviting Admin", role_name="Admin")
    async with async_session_factory() as session:
        admin_account_id = (
            await session.execute(select(User.account_id).where(User.id == admin_id))
        ).scalar_one()
    await grant_unlimited_plan(admin_account_id)
    invitee_email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as admin_client:
        invite_response = await admin_client.post(
            "/users/invitations", json={"email": invitee_email, "role_name": "Viewer"}
        )
    raw_token = invite_response.json()["token"]

    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        first_accept = await anon_client.post(
            "/users/invitations/accept",
            json={"token": raw_token, "password": "Invitee-Pass-123!", "full_name": "New Viewer"},
        )
        assert first_accept.status_code == 200

        second_accept = await anon_client.post(
            "/users/invitations/accept",
            json={"token": raw_token, "password": "Whatever-123!", "full_name": "Replay Attempt"},
        )

    assert second_accept.status_code == 400

    await _cleanup_invitation(invitee_email)
