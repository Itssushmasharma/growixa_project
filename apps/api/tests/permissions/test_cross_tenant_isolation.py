"""Cross-tenant isolation tests (GRX-SAAS-001 Phase A).

Two real accounts, two real users, real Postgres. Proves account A can never see or act
on account B's data — not "should not", but actually cannot, via the real API surface —
and that a cross-account guess 404s (indistinguishable from "does not exist") rather than
403ing (which would leak that the id exists in some other account) or leaking data.

This is the regression guard for GRX-SAAS-001: if a future change ever drops an
account_id scoping filter anywhere, one of these tests fails. Kept as one file, organized
by module, rather than scattered across every module's own test file — this is the single
place to see everything this app currently guarantees about account isolation. Grows one
section per Phase A checkpoint (users/auth, company/brand, contacts, email/campaigns/
integrations, and now the cross-cutting group -- audit_logs/usage_records -- all done).
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from tests.conftest import grant_unlimited_plan

from growixa_api.ai.models import AIGeneration, AIProviderConnection
from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.billing.models import AccountCreditBalance, CouponCode, CouponRedemption
from growixa_api.brand.models import BrandProfile
from growixa_api.campaigns.models import Campaign, CampaignRecipient
from growixa_api.company.models import CompanyProfile
from growixa_api.config import get_settings
from growixa_api.contacts.models import Contact, SuppressionEntry, Tag
from growixa_api.db import async_session_factory
from growixa_api.email_delivery.models import EmailEvent, MessageDelivery
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.social.models import SocialConnection, SocialPost, SocialPostMedia
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
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


async def _clear_contacts_fixtures() -> None:
    # audit_logs rows for these actions reference actor_user_id with no ON DELETE CASCADE
    # (by design, see GRX-AUDIT-001) -- must go before account_factory's teardown deletes
    # the users those rows point to, same as _cleanup_invited_user above.
    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(
                AuditLog.entity_type.in_(("contact", "segment", "contact_import"))
            )
        )
        await session.execute(delete(SuppressionEntry))
        await session.execute(delete(Tag))
        await session.execute(delete(Contact))
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
    await grant_unlimited_plan(account_a)

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


# --- contacts (GRX-SAAS-001 contacts slice) ---


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_list_another_accounts_contacts(
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
            create_response = await client_b.post(
                "/contacts", json={"email": f"{uuid.uuid4()}@example.com"}
            )
            assert create_response.status_code == 201

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            list_response = await client_a.get("/contacts")

        assert list_response.status_code == 200
        assert list_response.json() == []
    finally:
        await _clear_contacts_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_404_not_403_viewing_another_accounts_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """A 403 here would leak "this id exists, you're just not allowed" -- matching the
    same 404-not-403 guarantee already enforced for users (see above)."""
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
            create_response = await client_b.post(
                "/contacts", json={"email": f"{uuid.uuid4()}@example.com"}
            )
            contact_b_id = create_response.json()["id"]

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            get_response = await client_a.get(f"/contacts/{contact_b_id}")
            update_response = await client_a.patch(
                f"/contacts/{contact_b_id}", json={"first_name": "Hijacked"}
            )

        assert get_response.status_code == 404
        assert update_response.status_code == 404
    finally:
        await _clear_contacts_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_same_email_is_allowed_across_two_different_accounts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """contacts.email is composite-unique on (account_id, email), not globally unique
    (unlike users.email) -- two different customers may each have their own contact at
    the same address. Proves the GRX-SAAS-001 uniqueness-constraint judgment call
    actually holds against the real API, not just the migration."""
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Account B Admin", role_name="Admin", account_id=account_b
    )
    shared_email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            response_a = await client_a.post("/contacts", json={"email": shared_email})

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            response_b = await client_b.post("/contacts", json={"email": shared_email})

        assert response_a.status_code == 201
        assert response_b.status_code == 201
        assert response_a.json()["id"] != response_b.json()["id"]
    finally:
        await _clear_contacts_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tag_name_can_be_reused_across_accounts_without_leaking(
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
    tag_name = "VIP"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            create_response = await client_b.post("/contacts/tags", json={"name": tag_name})
            assert create_response.status_code == 201

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            create_a_response = await client_a.post("/contacts/tags", json={"name": tag_name})
            list_a_response = await client_a.get("/contacts/tags")

        # Account A has never created this tag -- must succeed independently (composite
        # unique, not global), and its own list must show only its own row.
        assert create_a_response.status_code == 201
        assert list_a_response.status_code == 200
        tag_ids = {row["id"] for row in list_a_response.json()}
        assert tag_ids == {create_a_response.json()["id"]}
    finally:
        await _clear_contacts_fixtures()


# --- email/campaigns/integrations (GRX-SAAS-001 email slice) ---


async def _clear_email_fixtures() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(EmailEvent))
        await session.execute(delete(MessageDelivery))
        await session.execute(delete(CampaignRecipient))
        await session.execute(delete(Campaign))
        await session.execute(delete(Contact))
        await session.execute(delete(SenderIdentity))
        await session.execute(delete(EmailProviderConnection))
        await session.execute(delete(EmailTemplateVersion))
        await session.execute(delete(EmailTemplate))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_list_another_accounts_templates(
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
            create_response = await client_b.post(
                "/templates",
                json={"name": "B's Template", "subject": "Hi", "body_html": "<p>hi</p>"},
            )
            assert create_response.status_code == 201
            template_b_id = create_response.json()["id"]

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            list_response = await client_a.get("/templates")
            get_response = await client_a.get(f"/templates/{template_b_id}")

        assert list_response.status_code == 200
        assert list_response.json() == []
        assert get_response.status_code == 404
    finally:
        await _clear_email_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_404_not_403_on_another_accounts_campaign(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    # Super Admin: creating a connection/sender identity needs integrations.manage,
    # which per RBAC.md is Super-Admin-only.
    admin_b = await user_factory(
        full_name="Account B Super Admin", role_name="Super Admin", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            connection_response = await client_b.post(
                "/integrations/email-provider",
                json={
                    "name": "Account B Postmark",
                    "provider": "POSTMARK",
                    "smtp_host": "smtp.postmarkapp.com",
                    "smtp_port": 587,
                    "smtp_username": "token",
                    "smtp_password": "b-secret",
                },
            )
            assert connection_response.status_code == 201
            identity_response = await client_b.post(
                "/integrations/sender-identities",
                json={
                    "email_provider_connection_id": connection_response.json()["id"],
                    "from_email": "b@growixa.local",
                    "from_name": "Account B",
                },
            )
            assert identity_response.status_code == 201
            campaign_response = await client_b.post(
                "/campaigns",
                json={
                    "name": "B's Campaign",
                    "subject": "Hi",
                    "body_html": "<p>hi</p>",
                    "sender_identity_id": identity_response.json()["id"],
                    "recipient_type": "ALL_CONTACTS",
                },
            )
            assert campaign_response.status_code == 201
            campaign_b_id = campaign_response.json()["id"]

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            get_response = await client_a.get(f"/campaigns/{campaign_b_id}")
            edit_response = await client_a.patch(
                f"/campaigns/{campaign_b_id}", json={"subject": "Hijacked"}
            )

        assert get_response.status_code == 404
        assert edit_response.status_code == 404
    finally:
        await _clear_email_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_two_accounts_can_each_independently_activate_the_same_provider(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """The GRX-EMAIL-011 partial unique index on (provider) WHERE is_active became
    composite on (account_id, provider) for GRX-SAAS-001 -- proves two different
    accounts can each have their own active POSTMARK connection at the same time,
    and that each account's list only shows its own row."""
    account_a = await account_factory()
    account_b = await account_factory()
    # Super Admin: integrations.manage is Super-Admin-only per RBAC.md.
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Account B Super Admin", role_name="Super Admin", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            response_a = await client_a.post(
                "/integrations/email-provider",
                json={
                    "name": "Account A Postmark",
                    "provider": "POSTMARK",
                    "smtp_host": "smtp.postmarkapp.com",
                    "smtp_port": 587,
                    "smtp_username": "token",
                    "smtp_password": "a-secret",
                },
            )

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            response_b = await client_b.post(
                "/integrations/email-provider",
                json={
                    "name": "Account B Postmark",
                    "provider": "POSTMARK",
                    "smtp_host": "smtp.postmarkapp.com",
                    "smtp_port": 587,
                    "smtp_username": "token",
                    "smtp_password": "b-secret",
                },
            )
            list_b_response = await client_b.get("/integrations/email-providers")

        assert response_a.status_code == 201
        assert response_b.status_code == 201
        assert response_a.json()["id"] != response_b.json()["id"]
        assert list_b_response.status_code == 200
        assert [row["id"] for row in list_b_response.json()] == [response_b.json()["id"]]
    finally:
        await _clear_email_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postmark_webhook_only_updates_the_matching_accounts_own_delivery(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """`/webhooks/postmark` carries no account identifier of its own -- it resolves the
    account purely by matching Basic Auth credentials against every account's active
    POSTMARK connection (see email_delivery.services.verify_webhook_credentials). Proves
    that resolution is real isolation, not just "any valid credentials work": account B's
    correct credentials against account A's MessageID must not touch account A's row."""
    account_a = await account_factory()
    account_b = await account_factory()
    # Super Admin: integrations.manage is Super-Admin-only per RBAC.md.
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Account B Super Admin", role_name="Super Admin", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            connection_a = (
                await client_a.post(
                    "/integrations/email-provider",
                    json={
                        "name": "Account A Postmark",
                        "provider": "POSTMARK",
                        "smtp_host": "smtp.postmarkapp.com",
                        "smtp_port": 587,
                        "smtp_username": "token",
                        "smtp_password": "a-secret",
                    },
                )
            ).json()
            identity_a = (
                await client_a.post(
                    "/integrations/sender-identities",
                    json={
                        "email_provider_connection_id": connection_a["id"],
                        "from_email": "a@growixa.local",
                        "from_name": "Account A",
                    },
                )
            ).json()
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            connection_b = (
                await client_b.post(
                    "/integrations/email-provider",
                    json={
                        "name": "Account B Postmark",
                        "provider": "POSTMARK",
                        "smtp_host": "smtp.postmarkapp.com",
                        "smtp_port": 587,
                        "smtp_username": "token",
                        "smtp_password": "b-secret",
                    },
                )
            ).json()

        # Basic Auth needs the real (auto-generated) usernames too.
        async with async_session_factory() as session:
            conn_a_row = await session.get(EmailProviderConnection, uuid.UUID(connection_a["id"]))
            conn_b_row = await session.get(EmailProviderConnection, uuid.UUID(connection_b["id"]))
            assert conn_a_row is not None
            assert conn_b_row is not None
            assert conn_a_row.webhook_username is not None
            assert conn_b_row.webhook_username is not None
            wh_username_a = conn_a_row.webhook_username
            wh_username_b = conn_b_row.webhook_username

        # Build account A's own send-chain directly, matching test_email_delivery.py's
        # established fixture pattern.
        async with async_session_factory() as session:
            contact = Contact(account_id=account_a, email="recipient@example.com")
            session.add(contact)
            await session.flush()
            campaign = Campaign(
                account_id=account_a,
                name="A's Campaign",
                subject="Hi",
                body_html="<p>hi</p>",
                sender_identity_id=uuid.UUID(identity_a["id"]),
                recipient_type="ALL_CONTACTS",
                status="SENDING",
            )
            session.add(campaign)
            await session.flush()
            recipient = CampaignRecipient(
                account_id=account_a,
                campaign_id=campaign.id,
                contact_id=contact.id,
                email=contact.email,
                status="SENT",
            )
            session.add(recipient)
            await session.flush()
            delivery = MessageDelivery(
                account_id=account_a,
                campaign_recipient_id=recipient.id,
                provider_message_id="pm-A-only",
                status="SENT",
            )
            session.add(delivery)
            await session.commit()
            delivery_id = delivery.id

        async with AsyncClient(transport=transport, base_url="http://test") as public_client:
            # Account B's own (valid) credentials, against account A's MessageID -- must
            # not find or touch account A's delivery.
            wrong_account_response = await public_client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Delivery",
                    "MessageID": "pm-A-only",
                    "Recipient": "recipient@example.com",
                },
                auth=(wh_username_b, connection_b["webhook_password"]),
            )
            assert wrong_account_response.status_code == 200  # unmatched -- silent no-op

            async with async_session_factory() as session:
                delivery_after_wrong = await session.get(MessageDelivery, delivery_id)
                assert delivery_after_wrong is not None
                assert delivery_after_wrong.status == "SENT"  # untouched

            right_account_response = await public_client.post(
                "/webhooks/postmark",
                json={
                    "RecordType": "Delivery",
                    "MessageID": "pm-A-only",
                    "Recipient": "recipient@example.com",
                },
                auth=(wh_username_a, connection_a["webhook_password"]),
            )
            assert right_account_response.status_code == 200

            async with async_session_factory() as session:
                delivery_after_right = await session.get(MessageDelivery, delivery_id)
                assert delivery_after_right is not None
                assert delivery_after_right.status == "DELIVERED"
    finally:
        await _clear_email_fixtures()


# --- cross-cutting: audit_logs (GRX-SAAS-001 cross-cutting slice) ---
# usage_records has no read/list API at all (no repository/service/api layer exists for
# it -- see MASTER_TASK_TRACKER.md's GRX-SAAS-001 evidence), so there is no endpoint that
# could leak one account's usage data to another; nothing to test here beyond the NOT NULL
# account_id column itself (exercised indirectly by every worker send_campaign test).


async def _clear_audit_fixtures() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AuditLog))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_list_another_accounts_audit_log_entries(
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
    viewer_a = await user_factory(
        full_name="Account A Viewer", role_name="Viewer", account_id=account_a
    )
    viewer_b = await user_factory(
        full_name="Account B Viewer", role_name="Viewer", account_id=account_b
    )

    transport = ASGITransport(app=create_app())
    try:
        # A role change is a real, already-wired audit event (users/services.py's
        # "role.changed") -- generates one row per account, each carrying that account's
        # own account_id.
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            role_change_a = await client_a.patch(
                f"/users/{viewer_a}/role", json={"role_name": "Analyst"}
            )
            assert role_change_a.status_code == 200

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            role_change_b = await client_b.patch(
                f"/users/{viewer_b}/role", json={"role_name": "Analyst"}
            )
            assert role_change_b.status_code == 200

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            audit_response_a = await client_a.get("/audit", params={"entity_type": "user"})

        assert audit_response_a.status_code == 200
        entity_ids_a = {row["entity_id"] for row in audit_response_a.json()}
        assert str(viewer_a) in entity_ids_a
        assert str(viewer_b) not in entity_ids_a
    finally:
        await _clear_audit_fixtures()


# --- social (Slice 5, GRX-SOCIAL-002/004/005) ---


async def _clear_social_fixtures() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(SocialPostMedia))
        await session.execute(delete(SocialPost))
        await session.execute(delete(SocialConnection))
        await session.commit()


async def _create_social_connection(account_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = SocialConnection(
            account_id=account_id,
            provider="INSTAGRAM_BUSINESS",
            ig_business_account_id=f"ig-{uuid.uuid4()}",
            facebook_page_id=f"page-{uuid.uuid4()}",
            access_token_encrypted=encrypt_secret("fake-page-access-token"),
        )
        session.add(connection)
        await session.commit()
        return connection.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_list_another_accounts_social_connections(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    await _create_social_connection(account_b)

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            list_response = await client_a.get("/social/connections")

        assert list_response.status_code == 200
        assert list_response.json() == []
    finally:
        await _clear_social_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_404_not_403_on_another_accounts_social_post(
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
    connection_b = await _create_social_connection(account_b)

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            create_response = await client_b.post(
                "/social/posts",
                json={"social_connection_id": str(connection_b), "caption": "B's post"},
            )
            assert create_response.status_code == 201
            post_b_id = create_response.json()["id"]

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            get_response = await client_a.get(f"/social/posts/{post_b_id}")
            edit_response = await client_a.patch(
                f"/social/posts/{post_b_id}", json={"caption": "Hijacked"}
            )
            media_response = await client_a.post(
                f"/social/posts/{post_b_id}/media",
                files={"file": ("test.jpg", b"\xff\xd8\xff" + b"fake jpeg", "image/jpeg")},
            )

        assert get_response.status_code == 404
        assert edit_response.status_code == 404
        assert media_response.status_code == 404
    finally:
        await _clear_social_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_creating_a_post_against_another_accounts_connection_404s(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """A's own social.manage grant doesn't let A attach a post to B's connection just
    by guessing its id -- the connection lookup itself is account-scoped."""
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Admin", role_name="Admin", account_id=account_a
    )
    connection_b = await _create_social_connection(account_b)

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            create_response = await client_a.post(
                "/social/posts", json={"social_connection_id": str(connection_b)}
            )

        assert create_response.status_code == 404
    finally:
        await _clear_social_fixtures()


# --- ai (Slice 6, GRX-AI-002/004/006) ---


async def _clear_ai_fixtures() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(AIGeneration))
        await session.execute(delete(AIProviderConnection))
        await session.commit()


async def _create_ai_connection(account_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = AIProviderConnection(
            account_id=account_id,
            provider="OPENAI",
            api_key_encrypted=encrypt_secret("fake-api-key"),
            default_model="gpt-4o-mini",
        )
        session.add(connection)
        await session.commit()
        return connection.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_list_another_accounts_ai_connections(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    await _create_ai_connection(account_b)

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            list_response = await client_a.get("/ai/connections")

        assert list_response.status_code == 200
        assert list_response.json() == []
    finally:
        await _clear_ai_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_gets_404_not_403_deactivating_another_accounts_ai_connection(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    connection_b = await _create_ai_connection(account_b)

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            deactivate_response = await client_a.post(f"/ai/connections/{connection_b}/deactivate")

        assert deactivate_response.status_code == 404
    finally:
        await _clear_ai_fixtures()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_see_another_accounts_generation_history(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    manager_b = await user_factory(
        full_name="Account B Manager", role_name="Marketing Manager", account_id=account_b
    )

    async with async_session_factory() as session:
        session.add(
            AIGeneration(
                account_id=account_b,
                created_by_user_id=manager_b,
                capability="SUBJECT_LINE",
                prompt_template_key="subject_line.v1",
                input_context={"brief": "B's brief"},
                output={"text": "B's subject line"},
                provider="OPENAI",
                model="gpt-4o-mini",
                status="COMPLETE",
            )
        )
        await session.commit()

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            list_response = await client_a.get("/ai/generations")

        assert list_response.status_code == 200
        assert list_response.json() == []
    finally:
        await _clear_ai_fixtures()


# --- billing (Slice 7, GRX-BILL-002/GRX-SAAS-012) ---


async def _clear_billing_fixtures(coupon_ids: list[uuid.UUID]) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(CouponRedemption).where(CouponRedemption.coupon_code_id.in_(coupon_ids))
        )
        await session.execute(delete(CouponCode).where(CouponCode.id.in_(coupon_ids)))
        await session.execute(delete(AccountCreditBalance))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_cannot_see_another_accounts_credit_balance_via_subscription_view(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """GET /billing/subscription has no id parameter to guess -- it's always scoped to
    the caller's own account via the access-token cookie. This proves that scoping
    actually holds: crediting account B never surfaces in account A's own view."""
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    async with async_session_factory() as session:
        session.add(
            AccountCreditBalance(account_id=account_b, credit_type="AI_RUNS", remaining_credits=500)
        )
        await session.commit()

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            response = await client_a.get("/billing/subscription")

        assert response.status_code == 200
        balances = {
            b["credit_type"]: b["remaining_credits"] for b in response.json()["credit_balances"]
        }
        assert balances.get("AI_RUNS", 0) == 0
    finally:
        await _clear_billing_fixtures(coupon_ids=[])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_coupon_redemption_uniqueness_is_scoped_per_account_not_global(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
    platform_admin_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """The (coupon_code_id, account_id) uniqueness constraint (THREAT_MODEL.md T65) must
    not leak across accounts -- account B redeeming a code must never block account A
    from redeeming the same code, same shape as test_same_email_is_allowed_across_two_
    different_accounts above."""
    account_a = await account_factory()
    account_b = await account_factory()
    admin_a = await user_factory(
        full_name="Account A Super Admin", role_name="Super Admin", account_id=account_a
    )
    admin_b = await user_factory(
        full_name="Account B Super Admin", role_name="Super Admin", account_id=account_b
    )
    platform_admin_id = await platform_admin_factory(role="platform.owner")

    async with async_session_factory() as session:
        coupon = CouponCode(
            code="SHARED-ACROSS-ACCOUNTS",
            discount_type="CREDIT_GRANT",
            discount_value=10,
            credit_type="AI_RUNS",
            created_by_platform_admin_id=platform_admin_id,
        )
        session.add(coupon)
        await session.commit()
        coupon_id = coupon.id

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_a)
        ) as client_a:
            response_a = await client_a.post(
                "/billing/redeem-coupon", json={"code": "SHARED-ACROSS-ACCOUNTS"}
            )
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_b)
        ) as client_b:
            response_b = await client_b.post(
                "/billing/redeem-coupon", json={"code": "SHARED-ACROSS-ACCOUNTS"}
            )

        assert response_a.status_code == 201
        assert response_b.status_code == 201
    finally:
        await _clear_billing_fixtures(coupon_ids=[coupon_id])


async def test_agency_service_rejects_other_owner_before_reading_clients() -> None:
    from unittest.mock import AsyncMock

    from fastapi import HTTPException

    from growixa_api.agency.models import Agency
    from growixa_api.agency.services import get_agency_clients

    session = AsyncMock()
    session.get.return_value = Agency(id=uuid.uuid4(), owner_id=uuid.uuid4(), name="Other tenant")
    with pytest.raises(HTTPException) as caught:
        await get_agency_clients(session, session.get.return_value.id, uuid.uuid4())
    assert caught.value.status_code == 404
    session.execute.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_agency_rejects_unverified_existing_account_link() -> None:
    from unittest.mock import AsyncMock

    from fastapi import HTTPException

    from growixa_api.agency.models import Agency
    from growixa_api.agency.schemas import AgencyClientCreate
    from growixa_api.agency.services import create_agency_client

    user_id = uuid.uuid4()
    agency = Agency(id=uuid.uuid4(), owner_id=user_id, name="Owned agency")
    session = AsyncMock()
    session.get.return_value = agency
    with pytest.raises(HTTPException) as caught:
        await create_agency_client(
            session,
            agency.id,
            AgencyClientCreate(client_name="Unverified", account_id=uuid.uuid4()),
            user_id,
        )
    assert caught.value.status_code == 409
    session.add.assert_not_called()
    session.commit.assert_not_awaited()


async def test_inbox_websocket_rejects_missing_authentication() -> None:
    from unittest.mock import AsyncMock

    from fastapi import WebSocketException
    from starlette.websockets import WebSocket

    from growixa_api.inbox.router import websocket_endpoint

    websocket = WebSocket(
        {
            "type": "websocket",
            "headers": [(b"origin", b"http://localhost:3000")],
            "query_string": b"account_id=untrusted",
        }
    )
    session = AsyncMock()
    with pytest.raises(WebSocketException) as caught:
        await websocket_endpoint(websocket, session)
    assert caught.value.code == 1008
    session.execute.assert_not_awaited()


async def test_inbox_websocket_rejects_different_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import AsyncMock

    from fastapi import WebSocketException
    from starlette.websockets import WebSocket

    from growixa_api.inbox import router as inbox_router

    account_id = uuid.uuid4()
    monkeypatch.setattr(inbox_router, "get_current_user_id", AsyncMock(return_value=uuid.uuid4()))
    monkeypatch.setattr(inbox_router, "get_account_id_for_user", AsyncMock(return_value=account_id))
    connect = AsyncMock()
    monkeypatch.setattr(inbox_router.manager, "connect", connect)
    websocket = WebSocket(
        {
            "type": "websocket",
            "headers": [(b"origin", b"http://localhost:3000")],
            "query_string": f"account_id={uuid.uuid4()}".encode(),
        }
    )
    with pytest.raises(WebSocketException):
        await inbox_router.websocket_endpoint(websocket, AsyncMock())
    connect.assert_not_awaited()
