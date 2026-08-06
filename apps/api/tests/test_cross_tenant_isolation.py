"""Cross-tenant isolation tests (GRX-SAAS-001 Phase A).

Two real accounts, two real users, real Postgres. Proves account A can never see or act
on account B's data — not "should not", but actually cannot, via the real API surface —
and that a cross-account guess 404s (indistinguishable from "does not exist") rather than
403ing (which would leak that the id exists in some other account) or leaking data.

This is the regression guard for GRX-SAAS-001: if a future change ever drops an
account_id scoping filter anywhere, one of these tests fails. Kept as one file, organized
by module, rather than scattered across every module's own test file — this is the single
place to see everything this app currently guarantees about account isolation. Grows one
section per Phase A checkpoint (users/auth done; company/brand, contacts, email next).
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.brand.models import BrandProfile
from growixa_api.company.models import CompanyProfile
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.users.models import User


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_invited_user(user_id: str) -> None:
    # Not created via user_factory (it comes from the accept-invitation API call), so
    # nothing tracks it for teardown -- and its own audit_logs row (no ON DELETE CASCADE,
    # by design per GRX-AUDIT-001) would otherwise block account_factory's cascade delete.
    async with async_session_factory() as session:
        await session.execute(delete(AuditLog).where(AuditLog.actor_user_id == uuid.UUID(user_id)))
        await session.execute(delete(User).where(User.id == uuid.UUID(user_id)))
        await session.commit()


async def _clear_company_and_brand() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(BrandProfile))
        await session.execute(delete(CompanyProfile))
        await session.commit()


# --- users/auth (GRX-SAAS-001 users/auth slice) ---


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_list_another_accounts_users(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    user_b = await user_factory(
        full_name="Account B User", role_name="Viewer", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
    ) as client:
        response = await client.get("/users")

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()}
    assert str(admin_a) in ids
    assert str(user_b) not in ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_404_not_403_disabling_another_accounts_user(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """A 403 here would leak "this id exists, you're just not allowed" -- a real user id
    from another account. 404 is indistinguishable from a fully made-up UUID, matching
    every other account-scoped lookup in this codebase."""
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    user_b = await user_factory(
        full_name="Account B User", role_name="Viewer", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
    ) as client:
        response = await client.patch(f"/users/{user_b}/status", json={"status": "DISABLED"})

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_404_not_403_changing_another_accounts_user_role(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    user_b = await user_factory(
        full_name="Account B User", role_name="Viewer", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
    ) as client:
        response = await client.patch(f"/users/{user_b}/role", json={"role_name": "Analyst"})

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invited_user_joins_the_inviting_admins_account(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """An invitation's account_id comes from the inviting admin, not the accepting
    caller (who is unauthenticated and has no account yet) -- confirms the new user
    lands in the *inviter's* account, not some default."""
    account_a = await account_factory()
    admin_a = await user_factory(
        full_name="Inviting Admin", role_name="Admin", account_id=account_a
    )

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
    ) as client:
        invite_response = await client.post(
            "/users/invitations",
            json={"email": f"{uuid.uuid4()}@example.com", "role_name": "Viewer"},
        )
        assert invite_response.status_code == 201
        token = invite_response.json()["token"]

        accept_response = await client.post(
            "/users/invitations/accept",
            json={"token": token, "password": "Test-Password-123!", "full_name": "New Hire"},
        )
        assert accept_response.status_code == 200
        new_user_id = accept_response.json()["id"]

        list_response = await client.get("/users")

    assert list_response.status_code == 200
    ids = {row["id"] for row in list_response.json()}
    assert new_user_id in ids

    await _cleanup_invited_user(new_user_id)


# --- company/brand (GRX-SAAS-001 company/brand slice) ---


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_see_another_accounts_company_profile(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Account B Admin", role_name="Admin", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            put_response = await client_b.put("/company/profile", json={"name": "Account B Co"})
            assert put_response.status_code == 200

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            get_response = await client_a.get("/company/profile")

        # Account A has no company profile of its own -- must see null, never B's row.
        assert get_response.status_code == 200
        assert get_response.json() is None
    finally:
        await _clear_company_and_brand()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_see_another_accounts_brand_profile(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Account B Admin", role_name="Admin", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            await client_b.put("/company/profile", json={"name": "Account B Co"})
            brand_response = await client_b.put(
                "/brand/profile", json={"brand_voice": "Account B's own voice"}
            )
            assert brand_response.status_code == 200

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            # Account A has no company profile yet -- brand requires one first, per the
            # existing CompanyProfileRequiredError guard, proving this isn't accidentally
            # falling through to account B's company row.
            get_response = await client_a.get("/brand/profile")
            put_response = await client_a.put(
                "/brand/profile", json={"brand_voice": "Should not attach to B's company"}
            )

        assert get_response.status_code == 200
        assert get_response.json() is None
        assert put_response.status_code == 400
    finally:
        await _clear_company_and_brand()
