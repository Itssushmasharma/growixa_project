"""Campaign draft CRUD + targeting integration tests (GRX-EMAIL-003).

Integration-tier: exercises real Postgres and the real create_app() app. Prerequisite rows
(sender identity, template, segment, contact list) are inserted directly via the ORM rather
than through their own APIs, since setting those up isn't what this test file is verifying.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.campaigns.models import Campaign, CampaignRecipient, CampaignVersion
from growixa_api.config import get_settings
from growixa_api.contacts.models import ContactList, Segment
from growixa_api.db import async_session_factory
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _create_sender_identity() -> uuid.UUID:
    async with async_session_factory() as session:
        connection = EmailProviderConnection(
            provider="POSTMARK",
            smtp_host="smtp.postmarkapp.com",
            smtp_port=587,
            smtp_username="token",
            smtp_password_encrypted="encrypted",
        )
        session.add(connection)
        await session.flush()
        identity = SenderIdentity(
            email_provider_connection_id=connection.id,
            from_email="hello@growixa.local",
            from_name="Growixa",
        )
        session.add(identity)
        await session.commit()
        return identity.id


async def _create_template() -> uuid.UUID:
    async with async_session_factory() as session:
        template = EmailTemplate(name="Test Template")
        session.add(template)
        await session.flush()
        session.add(
            EmailTemplateVersion(
                template_id=template.id,
                version_number=1,
                subject="Hi",
                body_html="<p>hi</p>",
            )
        )
        await session.commit()
        return template.id


async def _create_segment() -> uuid.UUID:
    async with async_session_factory() as session:
        segment = Segment(name="Test Segment", type="SAVED")
        session.add(segment)
        await session.commit()
        return segment.id


async def _create_contact_list() -> uuid.UUID:
    async with async_session_factory() as session:
        contact_list = ContactList(name="Test List")
        session.add(contact_list)
        await session.commit()
        return contact_list.id


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(CampaignRecipient))
        await session.execute(delete(CampaignVersion))
        await session.execute(delete(Campaign))
        await session.execute(delete(Segment))
        await session.execute(delete(ContactList))
        await session.execute(delete(EmailTemplateVersion))
        await session.execute(delete(EmailTemplate))
        await session.execute(delete(SenderIdentity))
        await session.execute(delete(EmailProviderConnection))
        await session.commit()


@pytest.fixture
async def sender_identity_id() -> AsyncGenerator[uuid.UUID, None]:
    yield await _create_sender_identity()


def _campaign_payload(sender_identity_id: uuid.UUID, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Spring Sale",
        "subject": "Spring is here",
        "body_html": "<p>Save 20%</p>",
        "sender_identity_id": str(sender_identity_id),
        "recipient_type": "ALL_CONTACTS",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_an_all_contacts_campaign(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post("/campaigns", json=_campaign_payload(sender_identity_id))

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "DRAFT"
        assert body["recipient_type"] == "ALL_CONTACTS"
        assert body["recipient_segment_id"] is None
        assert body["recipient_list_id"] is None
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_a_segment_targeted_campaign(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    segment_id = await _create_segment()
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(
                "/campaigns",
                json=_campaign_payload(
                    sender_identity_id,
                    recipient_type="SEGMENT",
                    recipient_segment_id=str(segment_id),
                ),
            )

        assert response.status_code == 201
        body = response.json()
        assert body["recipient_type"] == "SEGMENT"
        assert body["recipient_segment_id"] == str(segment_id)
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_a_list_targeted_campaign_from_a_template(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    list_id = await _create_contact_list()
    template_id = await _create_template()
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            response = await client.post(
                "/campaigns",
                json=_campaign_payload(
                    sender_identity_id,
                    recipient_type="LIST",
                    recipient_list_id=str(list_id),
                    template_id=str(template_id),
                ),
            )

        assert response.status_code == 201
        body = response.json()
        assert body["recipient_type"] == "LIST"
        assert body["recipient_list_id"] == str(list_id)
        assert body["template_id"] == str(template_id)
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_recipient_targeting_shapes_are_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    segment_id = await _create_segment()
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            missing_segment = await client.post(
                "/campaigns",
                json=_campaign_payload(sender_identity_id, recipient_type="SEGMENT"),
            )
            both_set = await client.post(
                "/campaigns",
                json=_campaign_payload(
                    sender_identity_id,
                    recipient_type="ALL_CONTACTS",
                    recipient_segment_id=str(segment_id),
                ),
            )
            unknown_segment = await client.post(
                "/campaigns",
                json=_campaign_payload(
                    sender_identity_id,
                    recipient_type="SEGMENT",
                    recipient_segment_id=str(uuid.uuid4()),
                ),
            )

        assert missing_segment.status_code == 400
        assert both_set.status_code == 400
        assert unknown_segment.status_code == 400
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_rejects_unknown_sender_identity(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        response = await client.post("/campaigns", json=_campaign_payload(uuid.uuid4()))

    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_editing_a_draft_updates_fields_and_can_switch_targeting(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    segment_id = await _create_segment()
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            create_response = await client.post(
                "/campaigns", json=_campaign_payload(sender_identity_id)
            )
            campaign_id = create_response.json()["id"]

            edit_response = await client.patch(
                f"/campaigns/{campaign_id}",
                json={
                    "subject": "Updated subject",
                    "recipient_type": "SEGMENT",
                    "recipient_segment_id": str(segment_id),
                },
            )

        assert edit_response.status_code == 200
        body = edit_response.json()
        assert body["subject"] == "Updated subject"
        assert body["recipient_type"] == "SEGMENT"
        assert body["recipient_segment_id"] == str(segment_id)
        assert body["recipient_list_id"] is None
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_editing_a_non_draft_campaign_is_rejected(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    try:
        cookies = _access_token_cookie(manager_id)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=cookies
        ) as client:
            create_response = await client.post(
                "/campaigns", json=_campaign_payload(sender_identity_id)
            )
            campaign_id = create_response.json()["id"]

            async with async_session_factory() as session:
                campaign = await session.get(Campaign, uuid.UUID(campaign_id))
                assert campaign is not None
                campaign.status = "SENT"
                await session.commit()

            edit_response = await client.patch(
                f"/campaigns/{campaign_id}", json={"subject": "Should not apply"}
            )

        assert edit_response.status_code == 409
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_view_only_role_can_read_but_not_create_or_edit(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    sender_identity_id: uuid.UUID,
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
            create_response = await manager_client.post(
                "/campaigns", json=_campaign_payload(sender_identity_id)
            )
            campaign_id = create_response.json()["id"]

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies=_access_token_cookie(analyst_id),
        ) as analyst_client:
            list_response = await analyst_client.get("/campaigns")
            get_response = await analyst_client.get(f"/campaigns/{campaign_id}")
            create_attempt = await analyst_client.post(
                "/campaigns", json=_campaign_payload(sender_identity_id)
            )
            edit_attempt = await analyst_client.patch(
                f"/campaigns/{campaign_id}", json={"subject": "Hijacked"}
            )

        assert list_response.status_code == 200
        assert get_response.status_code == 200
        assert create_attempt.status_code == 403
        assert edit_attempt.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthenticated_requests_are_rejected(sender_identity_id: uuid.UUID) -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/campaigns")
        post_response = await client.post("/campaigns", json=_campaign_payload(sender_identity_id))

    assert list_response.status_code == 401
    assert post_response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_and_edit_unknown_campaign_returns_404(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    manager_id = await user_factory(full_name="Test Manager", role_name="Marketing Manager")
    cookies = _access_token_cookie(manager_id)
    transport = ASGITransport(app=create_app())
    unknown_id = uuid.uuid4()
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        get_response = await client.get(f"/campaigns/{unknown_id}")
        edit_response = await client.patch(f"/campaigns/{unknown_id}", json={"subject": "x"})

    assert get_response.status_code == 404
    assert edit_response.status_code == 404
