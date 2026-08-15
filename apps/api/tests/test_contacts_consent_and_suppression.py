"""Consent history and suppression list integration tests (GRX-CONTACT-005).

Integration-tier: exercises real Postgres, the real create_app() app, and the real seeded
roles from GRX-AUTH-001. Rows created by a test are cleaned up by that test.
"""

import uuid
from collections.abc import Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.audit.models import AuditLog
from growixa_api.config import get_settings
from growixa_api.contacts.models import ConsentRecord, Contact, SuppressionEntry
from growixa_api.db import async_session_factory


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_contact(*contact_ids: uuid.UUID) -> None:
    # Callers must clean up any SuppressionEntry referencing a contact_id here first (via
    # _cleanup_suppression) — that FK has no ON DELETE CASCADE (suppression is meant to
    # outlive a deleted contact, e.g. a hard bounce with no contact record at all), so
    # deleting the contact first would violate it.
    async with async_session_factory() as session:
        for contact_id in contact_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "contact", AuditLog.entity_id == contact_id
                )
            )
            await session.execute(
                delete(ConsentRecord).where(ConsentRecord.contact_id == contact_id)
            )
            await session.execute(delete(Contact).where(Contact.id == contact_id))
        await session.commit()


async def _cleanup_suppression(*emails: str) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            delete(SuppressionEntry)
            .where(SuppressionEntry.email.in_(emails))
            .returning(SuppressionEntry.id)
        )
        entry_ids = [row[0] for row in result.all()]
        for entry_id in entry_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "suppression_entry", AuditLog.entity_id == entry_id
                )
            )
        await session.commit()


async def _cleanup_audit_actions(actor_user_id: uuid.UUID, *actions: str) -> None:
    """For actions whose audit row's `entity_id` doesn't survive the test (the
    suppression_entries row it pointed at was already deleted, or it's a bulk action with
    no single entity_id at all) -- `_cleanup_suppression`'s entity_id-matched cleanup
    can't find these, so they're removed directly by actor + action instead."""
    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(
                AuditLog.actor_user_id == actor_user_id, AuditLog.action.in_(actions)
            )
        )
        await session.commit()


async def _cleanup_domain_suppression(*domains: str) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            delete(SuppressionEntry)
            .where(SuppressionEntry.domain.in_(domains))
            .returning(SuppressionEntry.id)
        )
        entry_ids = [row[0] for row in result.all()]
        for entry_id in entry_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "suppression_entry", AuditLog.entity_id == entry_id
                )
            )
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_record_consent_and_view_history(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])

            grant_resp = await client.post(
                f"/contacts/{contact_id}/consent",
                json={"channel": "EMAIL", "status": "GRANTED", "source": "signup_form"},
            )
            assert grant_resp.status_code == 201
            assert grant_resp.json()["status"] == "GRANTED"

            withdraw_resp = await client.post(
                f"/contacts/{contact_id}/consent",
                json={"channel": "EMAIL", "status": "WITHDRAWN"},
            )
            assert withdraw_resp.status_code == 201

            history_resp = await client.get(f"/contacts/{contact_id}/consent")
            history = history_resp.json()
            assert len(history) == 2
            # Most recent first — the withdrawal is the current status.
            assert history[0]["status"] == "WITHDRAWN"
            assert history[1]["status"] == "GRANTED"
            assert history[1]["source"] == "signup_form"
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_recording_consent_for_unknown_contact_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            f"/contacts/{uuid.uuid4()}/consent",
            json={"channel": "EMAIL", "status": "GRANTED"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_suppressing_an_email_flags_the_matching_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])
            assert contact_resp.json()["is_suppressed"] is False

            suppress_resp = await client.post(
                "/contacts/suppression",
                json={"email": email, "reason": "UNSUBSCRIBED", "contact_id": str(contact_id)},
            )
            assert suppress_resp.status_code == 201
            assert suppress_resp.json()["reason"] == "UNSUBSCRIBED"

            get_resp = await client.get(f"/contacts/{contact_id}")
            assert get_resp.json()["is_suppressed"] is True
    finally:
        await _cleanup_suppression(email)
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resuppressing_the_same_email_updates_in_place(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            first = await client.post(
                "/contacts/suppression", json={"email": email, "reason": "BOUNCED"}
            )
            assert first.status_code == 201
            first_id = first.json()["id"]

            second = await client.post(
                "/contacts/suppression", json={"email": email, "reason": "COMPLAINED"}
            )
            assert second.status_code == 201
            assert second.json()["id"] == first_id
            assert second.json()["reason"] == "COMPLAINED"

            list_resp = await client.get("/contacts/suppression")
            matching = [e for e in list_resp.json() if e["email"] == email]
            assert len(matching) == 1
            assert matching[0]["reason"] == "COMPLAINED"
    finally:
        await _cleanup_suppression(email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_suppression_allowed_with_no_matching_contact(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"hard-bounce-{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.post(
                "/contacts/suppression", json={"email": email, "reason": "BOUNCED"}
            )
        assert response.status_code == 201
        assert response.json()["contact_id"] is None
    finally:
        await _cleanup_suppression(email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_suppressing_with_unknown_contact_id_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/suppression",
            json={"email": email, "reason": "MANUAL", "contact_id": str(uuid.uuid4())},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_removing_a_suppression_entry_deletes_it(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    """GRX-SAAS-013 ad hoc pass: the frontend's Remove button already called this route
    before it existed on the backend at all -- a real, silently-broken bug, not new
    scope."""
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            create_resp = await client.post(
                "/contacts/suppression", json={"email": email, "reason": "MANUAL"}
            )
            entry_id = create_resp.json()["id"]

            delete_resp = await client.delete(f"/contacts/suppression/{entry_id}")
            assert delete_resp.status_code == 204

            list_resp = await client.get("/contacts/suppression")
            assert email not in [e["email"] for e in list_resp.json()]
    finally:
        await _cleanup_suppression(email)
        await _cleanup_audit_actions(admin_id, "contact.suppressed", "contact.unsuppressed")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_removing_an_unknown_suppression_entry_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.delete(f"/contacts/suppression/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_blocking_a_domain_creates_a_domain_only_entry(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    domain = f"{uuid.uuid4()}.example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            response = await client.post("/contacts/suppression/domains", json={"domain": domain})
        assert response.status_code == 201
        body = response.json()
        assert body["domain"] == domain
        assert body["email"] is None
        assert body["reason"] == "MANUAL"
    finally:
        await _cleanup_domain_suppression(domain)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_blocking_the_same_domain_twice_returns_the_existing_entry(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    domain = f"{uuid.uuid4()}.example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            first = await client.post("/contacts/suppression/domains", json={"domain": domain})
            second = await client.post("/contacts/suppression/domains", json={"domain": domain})
        assert first.json()["id"] == second.json()["id"]

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            list_resp = await client.get("/contacts/suppression")
        assert len([e for e in list_resp.json() if e["domain"] == domain]) == 1
    finally:
        await _cleanup_domain_suppression(domain)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_import_creates_entries_and_skips_existing_duplicates(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    already_suppressed = f"{uuid.uuid4()}@example.com"
    new_email_1 = f"{uuid.uuid4()}@example.com"
    new_email_2 = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            await client.post(
                "/contacts/suppression", json={"email": already_suppressed, "reason": "MANUAL"}
            )

            csv_body = f"email,note\n{already_suppressed},x\n{new_email_1},\n{new_email_2},\n\n"
            files = {"file": ("suppress.csv", csv_body, "text/csv")}
            response = await client.post("/contacts/suppression/import", files=files)

        assert response.status_code == 200
        body = response.json()
        assert body["created"] == 2
        assert body["skipped"] == 1
        assert body["total_rows"] == 3

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            list_resp = await client.get("/contacts/suppression")
        emails = {e["email"] for e in list_resp.json()}
        assert {already_suppressed, new_email_1, new_email_2} <= emails
    finally:
        await _cleanup_suppression(already_suppressed, new_email_1, new_email_2)
        await _cleanup_audit_actions(admin_id, "contact.suppression_bulk_imported")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_import_without_an_email_column_returns_400(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        files = {"file": ("suppress.csv", "not_email\nfoo@example.com\n", "text/csv")}
        response = await client.post("/contacts/suppression/import", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_export_returns_every_entry(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            await client.post("/contacts/suppression", json={"email": email, "reason": "MANUAL"})
            response = await client.get("/contacts/suppression/export")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert email in response.text
    finally:
        await _cleanup_suppression(email)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_can_view_but_not_record_consent_or_suppress(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    account_id = await account_factory()
    analyst_id = await user_factory(
        full_name="Test Analyst", role_name="Analyst", account_id=account_id
    )
    admin_id = await user_factory(
        full_name="Test Admin 2", role_name="Admin", account_id=account_id
    )
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as admin_client:
            contact_resp = await admin_client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])

        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
        ) as client:
            history_resp = await client.get(f"/contacts/{contact_id}/consent")
            suppression_list_resp = await client.get("/contacts/suppression")
            record_resp = await client.post(
                f"/contacts/{contact_id}/consent",
                json={"channel": "EMAIL", "status": "GRANTED"},
            )
            suppress_resp = await client.post(
                "/contacts/suppression", json={"email": email, "reason": "MANUAL"}
            )

        assert history_resp.status_code == 200
        assert suppression_list_resp.status_code == 200
        assert record_resp.status_code == 403
        assert suppress_resp.status_code == 403
    finally:
        if contact_id is not None:
            await _cleanup_contact(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_has_no_access_to_consent_or_suppression(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        suppression_resp = await client.get("/contacts/suppression")
        consent_resp = await client.get(f"/contacts/{uuid.uuid4()}/consent")

    assert suppression_resp.status_code == 403
    assert consent_resp.status_code == 403
