"""Social post CRUD, media validation, and publish/schedule/cancel integration tests
(GRX-SOCIAL-005/006/007).

Integration-tier: exercises real Postgres and the real create_app() app, same convention
as test_campaigns.py. The Instagram connection itself is inserted directly via the ORM
(GRX-SOCIAL-003's OAuth flow has its own dedicated test file, test_social_oauth.py) since
setting one up isn't what this file is verifying. publish/schedule hit real Compose
RabbitMQ (publish_job actually runs) — the worker-side consumption of those jobs is
covered by apps/worker's own test suite, not here.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.files import storage_client
from growixa_api.social import services as social_services
from growixa_api.social.models import SocialConnection, SocialPost, SocialPostMedia

_JPEG_BYTES = b"\xff\xd8\xff" + b"fake jpeg payload"


@pytest.fixture(autouse=True)
def _fake_provider_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """No live Supabase Storage account or RabbitMQ reachable from the host test
    environment — matches test_email_delivery.py's identical monkeypatched
    publish_job/provider convention (see AGENT_HANDOFF.md for the documented evidence
    gap). What's under test here is the post/media/dispatch service logic, not
    storage_client's or the job producer's own network calls."""

    async def _fake_upload(**kwargs: object) -> str:
        return (
            f"https://fake-supabase.test/storage/v1/object/public/social-media/{uuid.uuid4()}.jpg"
        )

    async def _fake_delete(**kwargs: object) -> None:
        return None

    async def _fake_publish_job(queue_name: str, envelope: object) -> None:
        return None

    monkeypatch.setattr(storage_client, "upload_object", _fake_upload)
    monkeypatch.setattr(storage_client, "delete_object", _fake_delete)
    monkeypatch.setattr(social_services, "publish_job", _fake_publish_job)


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


async def _create_connection(account_id: uuid.UUID) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = SocialConnection(
            account_id=account_id,
            provider="INSTAGRAM_BUSINESS",
            ig_business_account_id="ig-123",
            ig_username="growixa_test",
            facebook_page_id="page-123",
            access_token_encrypted=encrypt_secret("fake-page-access-token"),
        )
        session.add(connection)
        await session.commit()
        return connection.id


async def _cleanup() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(SocialPostMedia))
        await session.execute(delete(SocialPost))
        await session.execute(delete(SocialConnection))
        await session.commit()


@pytest.fixture
async def social_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


@pytest.fixture
async def social_connection_id(social_account_id: uuid.UUID) -> AsyncGenerator[uuid.UUID, None]:
    yield await _create_connection(social_account_id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_manager_can_create_a_draft_post_and_add_and_remove_media(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post(
                "/social/posts",
                json={"social_connection_id": str(social_connection_id), "caption": "Hello world"},
            )
            assert create_response.status_code == 201
            post = create_response.json()
            assert post["status"] == "DRAFT"
            assert post["media"] == []
            post_id = post["id"]

            media_response = await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("test.jpg", _JPEG_BYTES, "image/jpeg")},
            )
            assert media_response.status_code == 201
            media_id = media_response.json()["id"]

            get_response = await client.get(f"/social/posts/{post_id}")
            assert len(get_response.json()["media"]) == 1

            delete_response = await client.delete(f"/social/posts/{post_id}/media/{media_id}")
            assert delete_response.status_code == 204

            get_response_2 = await client.get(f"/social/posts/{post_id}")
            assert get_response_2.json()["media"] == []
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_media_upload_rejects_non_jpeg(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            post_id = create_response.json()["id"]

            media_response = await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("test.png", b"\x89PNG fake png data", "image/png")},
            )
            assert media_response.status_code == 400
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_media_upload_rejects_a_second_item(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            post_id = create_response.json()["id"]

            first = await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("a.jpg", _JPEG_BYTES, "image/jpeg")},
            )
            assert first.status_code == 201

            second = await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("b.jpg", _JPEG_BYTES, "image/jpeg")},
            )
            assert second.status_code == 400
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_content_creator_can_draft_but_not_publish(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    creator_id = await user_factory(
        full_name="Test Creator", role_name="Content Creator", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(creator_id)
        ) as client:
            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            assert create_response.status_code == 201
            post_id = create_response.json()["id"]

            await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("test.jpg", _JPEG_BYTES, "image/jpeg")},
            )

            publish_response = await client.post(f"/social/posts/{post_id}/publish")
            assert publish_response.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_publish_now_requires_at_least_one_media_item(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            post_id = create_response.json()["id"]

            publish_response = await client.post(f"/social/posts/{post_id}/publish")
            assert publish_response.status_code == 400
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_publish_now_transitions_the_post_to_dispatching(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            post_id = create_response.json()["id"]
            await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("test.jpg", _JPEG_BYTES, "image/jpeg")},
            )

            publish_response = await client.post(f"/social/posts/{post_id}/publish")
            assert publish_response.status_code == 202
            assert "job_id" in publish_response.json()

            get_response = await client.get(f"/social/posts/{post_id}")
            assert get_response.json()["status"] == "DISPATCHING"

            second_publish = await client.post(f"/social/posts/{post_id}/publish")
            assert second_publish.status_code == 409
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schedule_then_cancel_flow(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            post_id = create_response.json()["id"]
            await client.post(
                f"/social/posts/{post_id}/media",
                files={"file": ("test.jpg", _JPEG_BYTES, "image/jpeg")},
            )

            future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
            schedule_response = await client.post(
                f"/social/posts/{post_id}/schedule", json={"scheduled_at": future}
            )
            assert schedule_response.status_code == 200
            assert schedule_response.json()["status"] == "SCHEDULED"

            cancel_response = await client.post(f"/social/posts/{post_id}/cancel")
            assert cancel_response.status_code == 200
            assert cancel_response.json()["status"] == "CANCELLED"

            retry_response = await client.post(f"/social/posts/{post_id}/retry")
            assert retry_response.status_code == 409
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyst_view_only_gets_403_on_write_actions(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    social_connection_id: uuid.UUID,
) -> None:
    analyst_id = await user_factory(
        full_name="Test Analyst", role_name="Analyst", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(analyst_id)
        ) as client:
            list_response = await client.get("/social/posts")
            assert list_response.status_code == 200

            create_response = await client.post(
                "/social/posts", json={"social_connection_id": str(social_connection_id)}
            )
            assert create_response.status_code == 403
    finally:
        await _cleanup()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_unknown_post_404s(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Test Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
        ) as client:
            response = await client.get(f"/social/posts/{uuid.uuid4()}")
            assert response.status_code == 404
    finally:
        await _cleanup()
