"""Segment integration tests (GRX-CONTACT-003).

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
from growixa_api.campaigns.models import Campaign
from growixa_api.config import get_settings
from growixa_api.contacts.models import (
    Contact,
    ContactTag,
    Segment,
    SegmentMember,
    SegmentRule,
    Tag,
)
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.users.models import User


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _cleanup_contacts(*contact_ids: uuid.UUID) -> None:
    async with async_session_factory() as session:
        for contact_id in contact_ids:
            await session.execute(
                delete(AuditLog).where(
                    AuditLog.entity_type == "contact", AuditLog.entity_id == contact_id
                )
            )
            await session.execute(delete(ContactTag).where(ContactTag.contact_id == contact_id))
            await session.execute(
                delete(SegmentMember).where(SegmentMember.contact_id == contact_id)
            )
            await session.execute(delete(Contact).where(Contact.id == contact_id))
        await session.commit()


async def _cleanup_tag(name: str) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(Tag).where(Tag.name == name))
        await session.commit()


async def _cleanup_segment(segment_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(AuditLog).where(
                AuditLog.entity_type == "segment", AuditLog.entity_id == segment_id
            )
        )
        await session.execute(delete(SegmentMember).where(SegmentMember.segment_id == segment_id))
        await session.execute(delete(SegmentRule).where(SegmentRule.segment_id == segment_id))
        await session.execute(delete(Segment).where(Segment.id == segment_id))
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dynamic_segment_reflects_new_matches_live(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    tag_name = f"seg-tag-{uuid.uuid4().hex[:8]}"
    email_a = f"{uuid.uuid4()}@example.com"
    email_b = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_a_id: uuid.UUID | None = None
    contact_b_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            tag_resp = await client.post("/contacts/tags", json={"name": tag_name})
            tag_id = tag_resp.json()["id"]

            contact_a = await client.post("/contacts", json={"email": email_a})
            contact_a_id = uuid.UUID(contact_a.json()["id"])
            await client.post(f"/contacts/{contact_a_id}/tags", json={"tag_id": tag_id})

            segment_resp = await client.post(
                "/contacts/segments",
                json={
                    "name": "Dynamic tagged",
                    "type": "DYNAMIC",
                    "rules": [{"field": "tag", "operator": "equals", "value": tag_name}],
                },
            )
            assert segment_resp.status_code == 201
            assert segment_resp.json()["member_count"] == 1
            segment_id = uuid.UUID(segment_resp.json()["id"])

            # Tag a second contact after the segment was created — a DYNAMIC segment
            # should pick it up live, with no resave step.
            contact_b = await client.post("/contacts", json={"email": email_b})
            contact_b_id = uuid.UUID(contact_b.json()["id"])
            await client.post(f"/contacts/{contact_b_id}/tags", json={"tag_id": tag_id})

            get_resp = await client.get(f"/contacts/segments/{segment_id}")
            assert get_resp.json()["member_count"] == 2

            members_resp = await client.get(f"/contacts/segments/{segment_id}/members")
            member_emails = {m["email"] for m in members_resp.json()}
            assert member_emails == {email_a.lower(), email_b.lower()}
    finally:
        if segment_id is not None:
            await _cleanup_segment(segment_id)
        await _cleanup_contacts(*(cid for cid in (contact_a_id, contact_b_id) if cid))
        await _cleanup_tag(tag_name)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_saved_segment_freezes_membership_at_creation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    tag_name = f"seg-tag-{uuid.uuid4().hex[:8]}"
    email_a = f"{uuid.uuid4()}@example.com"
    email_b = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_a_id: uuid.UUID | None = None
    contact_b_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            tag_resp = await client.post("/contacts/tags", json={"name": tag_name})
            tag_id = tag_resp.json()["id"]

            contact_a = await client.post("/contacts", json={"email": email_a})
            contact_a_id = uuid.UUID(contact_a.json()["id"])
            await client.post(f"/contacts/{contact_a_id}/tags", json={"tag_id": tag_id})

            segment_resp = await client.post(
                "/contacts/segments",
                json={
                    "name": "Saved snapshot",
                    "type": "SAVED",
                    "rules": [{"field": "tag", "operator": "equals", "value": tag_name}],
                },
            )
            assert segment_resp.status_code == 201
            assert segment_resp.json()["member_count"] == 1
            segment_id = uuid.UUID(segment_resp.json()["id"])

            # A contact tagged after a SAVED segment is created must NOT show up in it —
            # membership is frozen at creation time, not re-evaluated on read.
            contact_b = await client.post("/contacts", json={"email": email_b})
            contact_b_id = uuid.UUID(contact_b.json()["id"])
            await client.post(f"/contacts/{contact_b_id}/tags", json={"tag_id": tag_id})

            get_resp = await client.get(f"/contacts/segments/{segment_id}")
            assert get_resp.json()["member_count"] == 1

            members_resp = await client.get(f"/contacts/segments/{segment_id}/members")
            member_emails = {m["email"] for m in members_resp.json()}
            assert member_emails == {email_a.lower()}
    finally:
        if segment_id is not None:
            await _cleanup_segment(segment_id)
        await _cleanup_contacts(*(cid for cid in (contact_a_id, contact_b_id) if cid))
        await _cleanup_tag(tag_name)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_status_rule_matches_active_contacts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])

            segment_resp = await client.post(
                "/contacts/segments",
                json={
                    "name": "Active contacts",
                    "type": "DYNAMIC",
                    "rules": [{"field": "status", "operator": "equals", "value": "ACTIVE"}],
                },
            )
            segment_id = uuid.UUID(segment_resp.json()["id"])

            members_resp = await client.get(f"/contacts/segments/{segment_id}/members")
            assert email.lower() in {m["email"] for m in members_resp.json()}

            await client.patch(f"/contacts/{contact_id}/status", json={"status": "ARCHIVED"})

            members_after = await client.get(f"/contacts/segments/{segment_id}/members")
            assert email.lower() not in {m["email"] for m in members_after.json()}
    finally:
        if segment_id is not None:
            await _cleanup_segment(segment_id)
        if contact_id is not None:
            await _cleanup_contacts(contact_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unsupported_field_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/segments",
            json={
                "name": "Bad field",
                "type": "DYNAMIC",
                "rules": [{"field": "consent_status", "operator": "equals", "value": "x"}],
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unsupported_operator_for_field_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/segments",
            json={
                "name": "Bad operator",
                "type": "DYNAMIC",
                "rules": [{"field": "status", "operator": "contains", "value": "ACT"}],
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unknown_custom_field_key_in_rule_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/segments",
            json={
                "name": "Bad custom field",
                "type": "DYNAMIC",
                "rules": [
                    {"field": "custom_field:does_not_exist", "operator": "equals", "value": "x"}
                ],
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_created_at_date_value_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/contacts/segments",
            json={
                "name": "Bad date",
                "type": "DYNAMIC",
                "rules": [{"field": "created_at", "operator": "after", "value": "not-a-date"}],
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_can_view_but_not_create_segments(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    analyst_id = await user_factory(full_name="Test Analyst", role_name="Analyst")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
    ) as client:
        list_response = await client.get("/contacts/segments")
        create_response = await client.post(
            "/contacts/segments", json={"name": "x", "type": "DYNAMIC", "rules": []}
        )

    assert list_response.status_code == 200
    assert create_response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_viewer_has_no_access_to_segments(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    viewer_id = await user_factory(full_name="Test Viewer", role_name="Viewer")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        response = await client.get("/contacts/segments")

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tag_contains_operator_evaluates_matches(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    tag_name = f"beta-tester-{uuid.uuid4().hex[:6]}"
    email = f"{uuid.uuid4()}@example.com"

    transport = ASGITransport(app=create_app())
    contact_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            tag_resp = await client.post("/contacts/tags", json={"name": tag_name})
            tag_id = tag_resp.json()["id"]

            contact_resp = await client.post("/contacts", json={"email": email})
            contact_id = uuid.UUID(contact_resp.json()["id"])
            await client.post(f"/contacts/{contact_id}/tags", json={"tag_id": tag_id})

            # Create dynamic segment using "contains" on tag (e.g. "beta")
            segment_resp = await client.post(
                "/contacts/segments",
                json={
                    "name": "Beta users",
                    "type": "DYNAMIC",
                    "rules": [{"field": "tag", "operator": "contains", "value": "beta-test"}],
                },
            )
            assert segment_resp.status_code == 201
            segment_id = uuid.UUID(segment_resp.json()["id"])
            assert segment_resp.json()["member_count"] == 1

            # Fetch members
            members_resp = await client.get(f"/contacts/segments/{segment_id}/members")
            assert members_resp.status_code == 200
            assert len(members_resp.json()) == 1
            assert members_resp.json()[0]["email"] == email
    finally:
        if segment_id:
            await _cleanup_segment(segment_id)
        if contact_id:
            await _cleanup_contacts(contact_id)
        await _cleanup_tag(tag_name)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_segment_name_type_and_rules(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    email_a = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    email_b = f"bob_{uuid.uuid4().hex[:6]}@example.com"

    transport = ASGITransport(app=create_app())
    contact_a_id: uuid.UUID | None = None
    contact_b_id: uuid.UUID | None = None
    segment_id: uuid.UUID | None = None
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            resp_a = await client.post("/contacts", json={"email": email_a, "first_name": "Alice"})
            contact_a_id = uuid.UUID(resp_a.json()["id"])
            resp_b = await client.post("/contacts", json={"email": email_b, "first_name": "Bob"})
            contact_b_id = uuid.UUID(resp_b.json()["id"])

            # Create initial segment matching Alice
            create_resp = await client.post(
                "/contacts/segments",
                json={
                    "name": "Initial Segment",
                    "type": "DYNAMIC",
                    "rules": [{"field": "first_name", "operator": "equals", "value": "Alice"}],
                },
            )
            assert create_resp.status_code == 201
            segment_id = uuid.UUID(create_resp.json()["id"])
            assert create_resp.json()["member_count"] == 1

            # Update segment to match Bob instead and switch to SAVED
            update_resp = await client.put(
                f"/contacts/segments/{segment_id}",
                json={
                    "name": "Updated Segment",
                    "type": "SAVED",
                    "rules": [{"field": "first_name", "operator": "equals", "value": "Bob"}],
                },
            )
            assert update_resp.status_code == 200
            data = update_resp.json()
            assert data["name"] == "Updated Segment"
            assert data["type"] == "SAVED"
            assert data["member_count"] == 1

            # Verify members list returns Bob
            members_resp = await client.get(f"/contacts/segments/{segment_id}/members")
            assert members_resp.status_code == 200
            assert len(members_resp.json()) == 1
            assert members_resp.json()[0]["email"] == email_b
    finally:
        if segment_id:
            await _cleanup_segment(segment_id)
        if contact_a_id and contact_b_id:
            await _cleanup_contacts(contact_a_id, contact_b_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_segment_succeeds_when_not_in_use(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        # Create segment
        create_resp = await client.post(
            "/contacts/segments",
            json={"name": "To Delete", "type": "DYNAMIC", "rules": []},
        )
        assert create_resp.status_code == 201
        segment_id = uuid.UUID(create_resp.json()["id"])

        # Delete segment
        del_resp = await client.delete(f"/contacts/segments/{segment_id}")
        assert del_resp.status_code == 204

        # Confirm 404 on get
        get_resp = await client.get(f"/contacts/segments/{segment_id}")
        assert get_resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_segment_blocked_when_targeted_by_active_campaign(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    segment_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    conn_id: uuid.UUID | None = None
    identity_id: uuid.UUID | None = None

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
        ) as client:
            # 1. Create Segment
            create_resp = await client.post(
                "/contacts/segments",
                json={"name": "Target Segment", "type": "DYNAMIC", "rules": []},
            )
            assert create_resp.status_code == 201
            segment_id = uuid.UUID(create_resp.json()["id"])

            # 2. Setup SMTP Connection, Sender Identity & Campaign referencing segment
            async with async_session_factory() as session:
                admin_user = await session.get(User, admin_id)
                assert admin_user is not None
                account_id = admin_user.account_id

                conn = EmailProviderConnection(
                    account_id=account_id,
                    name=f"test-conn-{uuid.uuid4().hex[:6]}",
                    provider="POSTMARK",
                    smtp_host="smtp.postmarkapp.com",
                    smtp_port=587,
                    smtp_username="token",
                    smtp_password_encrypted="enc",
                )
                session.add(conn)
                await session.flush()
                conn_id = conn.id

                identity = SenderIdentity(
                    account_id=account_id,
                    email_provider_connection_id=conn.id,
                    from_email="sender@test.local",
                    from_name="Sender",
                )
                session.add(identity)
                await session.flush()
                identity_id = identity.id

                campaign = Campaign(
                    account_id=account_id,
                    name="Active Summer Sale",
                    subject="Sale!",
                    body_html="<p>Sale</p>",
                    sender_identity_id=identity.id,
                    recipient_type="SEGMENT",
                    recipient_segment_id=segment_id,
                    status="SCHEDULED",
                    created_by_user_id=admin_id,
                )
                session.add(campaign)
                await session.commit()
                campaign_id = campaign.id

            # 3. Attempt to delete segment -> must fail with 409 Conflict
            del_resp = await client.delete(f"/contacts/segments/{segment_id}")
            assert del_resp.status_code == 409
            error_data = del_resp.json()
            assert "Cannot delete segment" in error_data["detail"]
            assert "Active Summer Sale" in error_data["detail"]
            assert "SCHEDULED" in error_data["detail"]

            # 4. Change campaign status to SENT (completed) -> deletion now succeeds and unlinks
            async with async_session_factory() as session:
                campaign_obj = await session.get(Campaign, campaign_id)
                assert campaign_obj is not None
                campaign_obj.status = "SENT"
                await session.commit()

            del_resp_2 = await client.delete(f"/contacts/segments/{segment_id}")
            assert del_resp_2.status_code == 204

            # Verify campaign's recipient_segment_id was unlinked to None
            async with async_session_factory() as session:
                campaign_obj = await session.get(Campaign, campaign_id)
                assert campaign_obj is not None
                assert campaign_obj.recipient_segment_id is None
    finally:
        async with async_session_factory() as session:
            if campaign_id:
                await session.execute(delete(Campaign).where(Campaign.id == campaign_id))
            if identity_id:
                await session.execute(
                    delete(SenderIdentity).where(SenderIdentity.id == identity_id)
                )
            if conn_id:
                await session.execute(
                    delete(EmailProviderConnection).where(EmailProviderConnection.id == conn_id)
                )
            if segment_id:
                await session.execute(
                    delete(SegmentRule).where(SegmentRule.segment_id == segment_id)
                )
                await session.execute(delete(Segment).where(Segment.id == segment_id))
            await session.commit()
