"""Phase 4 Social Media Engine integration tests.
Tests multi-channel adapters (LinkedIn, Twitter/X, Instagram, Facebook, YouTube),
channel capabilities, post creation with UTM parameters, bulk scheduling with
rate-limit staggering, connection disconnection, and the media library.
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

pytestmark = pytest.mark.integration

from growixa_api.app import create_app
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.config import get_settings
from growixa_api.db import async_session_factory
from growixa_api.files import storage_client
from growixa_api.media.models import MediaAsset, MediaFolder
from growixa_api.social import services as social_services
from growixa_api.social.models import SocialConnection, SocialPost, SocialPostMedia
from growixa_api.social.providers.factory import get_social_provider, list_available_channels
from growixa_api.social.providers.linkedin import LinkedInSocialProvider
from growixa_api.social.providers.twitter import TwitterSocialProvider

_JPEG_BYTES = b"\xff\xd8\xff" + b"fake jpeg payload for phase 4"


@pytest.fixture(autouse=True)
def _fake_provider_calls(monkeypatch: pytest.MonkeyPatch) -> None:
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


async def _create_test_connection(
    account_id: uuid.UUID,
    provider: str = "LINKEDIN",
    account_name: str = "Growixa Test Org",
    username: str = "growixa_org",
) -> uuid.UUID:
    async with async_session_factory() as session:
        connection = SocialConnection(
            account_id=account_id,
            provider=provider,
            provider_account_id=f"urn:li:org:{uuid.uuid4()}",
            provider_account_name=account_name,
            provider_username=username,
            access_token_encrypted=encrypt_secret("test-access-token"),
            refresh_token_encrypted=encrypt_secret("test-refresh-token"),
            is_active=True,
        )
        session.add(connection)
        await session.commit()
        return connection.id


@pytest.fixture
async def social_account_id(
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> AsyncGenerator[uuid.UUID, None]:
    yield await account_factory()


@pytest.fixture
async def cleanup_db() -> AsyncGenerator[None, None]:
    yield
    async with async_session_factory() as session:
        await session.execute(delete(MediaAsset))
        await session.execute(delete(MediaFolder))
        await session.execute(delete(SocialPostMedia))
        await session.execute(delete(SocialPost))
        await session.execute(delete(SocialConnection))
        await session.commit()


def test_provider_capabilities_and_post_validation() -> None:
    channels = list_available_channels()
    names = [c.provider_name for c in channels]
    assert "LINKEDIN" in names
    assert "TWITTER" in names
    assert "INSTAGRAM_BUSINESS" in names
    assert "FACEBOOK_PAGE" in names
    assert "YOUTUBE" in names

    # Test LinkedIn: text allowed, 3000 max
    li = LinkedInSocialProvider()
    assert li.capabilities.max_characters == 3000
    assert not li.capabilities.requires_media
    assert li.validate_post("Hello LinkedIn", []) == []
    assert len(li.validate_post("X" * 3001, [])) == 1

    # Test Twitter: 280 max, 4 media items max
    tw = TwitterSocialProvider()
    assert tw.capabilities.max_characters == 280
    assert tw.capabilities.max_media_count == 4
    assert tw.validate_post("Hello X", []) == []
    assert len(tw.validate_post("X" * 281, [])) == 1

    # Test Instagram: requires media
    ig = get_social_provider("INSTAGRAM_BUSINESS")
    assert ig.capabilities.requires_media
    errors = ig.validate_post("Caption without media", [])
    assert len(errors) == 1
    assert "requires at least one media item" in errors[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_channels_endpoint(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
) -> None:
    viewer_id = await user_factory(
        full_name="Social Viewer", role_name="Marketing Manager", account_id=social_account_id
    )
    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(viewer_id)
    ) as client:
        resp = await client.get("/social/channels")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 5
        provider_names = {item["provider_name"] for item in data}
        assert "LINKEDIN" in provider_names
        assert "TWITTER" in provider_names
        assert "INSTAGRAM_BUSINESS" in provider_names
        assert "FACEBOOK_PAGE" in provider_names
        assert "YOUTUBE" in provider_names


@pytest.mark.asyncio
@pytest.mark.integration
async def test_connection_management_and_disconnect(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Social Manager", role_name="Marketing Manager", account_id=social_account_id
    )
    conn_id = await _create_test_connection(
        social_account_id, provider="TWITTER", username="growixa_x"
    )

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
    ) as client:
        # List connections
        resp = await client.get("/social/connections")
        assert resp.status_code == 200
        connections = resp.json()
        assert any(c["id"] == str(conn_id) for c in connections)

        # Disconnect
        del_resp = await client.delete(f"/social/connections/{conn_id}")
        assert del_resp.status_code == 204

        # Listing again should show it deactivated
        resp2 = await client.get("/social/connections")
        conn_dict = next(c for c in resp2.json() if c["id"] == str(conn_id))
        assert conn_dict["is_active"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_post_with_utm_and_length_validation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Post Creator", role_name="Marketing Manager", account_id=social_account_id
    )
    tw_conn_id = await _create_test_connection(social_account_id, provider="TWITTER")
    li_conn_id = await _create_test_connection(social_account_id, provider="LINKEDIN")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
    ) as client:
        # 1. Reject Twitter post exceeding 280 chars
        long_caption = "X" * 281
        resp_too_long = await client.post(
            "/social/posts",
            json={"social_connection_id": str(tw_conn_id), "caption": long_caption},
        )
        assert resp_too_long.status_code == 400
        assert "cannot exceed 280 characters" in resp_too_long.text

        # 2. Accept LinkedIn post with 500 chars and UTM params
        resp_li = await client.post(
            "/social/posts",
            json={
                "social_connection_id": str(li_conn_id),
                "caption": "P" * 500,
                "utm_source": "linkedin",
                "utm_medium": "social",
                "utm_campaign": "launch2026",
            },
        )
        assert resp_li.status_code == 201
        post_data = resp_li.json()
        assert post_data["caption"] == "P" * 500
        assert post_data["utm_source"] == "linkedin"
        assert post_data["utm_medium"] == "social"
        assert post_data["utm_campaign"] == "launch2026"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_schedule_posts(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
) -> None:
    manager_id = await user_factory(
        full_name="Bulk Scheduler User", role_name="Marketing Manager", account_id=social_account_id
    )
    conn_id = await _create_test_connection(social_account_id, provider="LINKEDIN")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(manager_id)
    ) as client:
        future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
        payload = {
            "stagger_interval_minutes": 15,
            "items": [
                {
                    "social_connection_id": str(conn_id),
                    "caption": "Post 1 for LinkedIn",
                    "scheduled_at": future_time,
                    "utm_campaign": "batch1",
                },
                {
                    "social_connection_id": str(conn_id),
                    "caption": "Post 2 for LinkedIn",
                    "scheduled_at": future_time,
                    "utm_campaign": "batch1",
                },
            ],
        }
        resp = await client.post("/social/bulk-schedule", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_requested"] == 2
        assert data["scheduled_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["scheduled_posts"]) == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_media_library_crud_and_isolation(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    social_account_id: uuid.UUID,
    account_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(
        full_name="Media User", role_name="Marketing Manager", account_id=social_account_id
    )
    other_account_id = await account_factory()
    other_user_id = await user_factory(
        full_name="Other User", role_name="Marketing Manager", account_id=other_account_id
    )

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(user_id)
    ) as client:
        # 1. Create a folder
        folder_resp = await client.post(
            "/media/folders", json={"name": "Campaign Assets", "color": "#4F46E5"}
        )
        assert folder_resp.status_code == 201
        folder_data = folder_resp.json()
        folder_id = folder_data["id"]
        assert folder_data["name"] == "Campaign Assets"

        # 2. Upload an image into the folder
        upload_resp = await client.post(
            "/media/upload",
            data={"folder_id": folder_id, "caption": "Launch Banner"},
            files={"file": ("banner.jpg", _JPEG_BYTES, "image/jpeg")},
        )
        assert upload_resp.status_code == 201
        asset_data = upload_resp.json()
        asset_id = asset_data["id"]
        assert asset_data["file_name"] == "banner.jpg"
        assert asset_data["media_type"] == "IMAGE"
        assert asset_data["folder_id"] == folder_id

        # 3. List media
        list_resp = await client.get("/media")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total_assets"] == 1
        assert list_data["assets"][0]["id"] == asset_id

        # 4. Verify account isolation: other user sees 0 assets and 0 folders
        async with AsyncClient(
            transport=transport, base_url="http://test", cookies=_access_token_cookie(other_user_id)
        ) as other_client:
            other_media_resp = await other_client.get("/media")
            assert other_media_resp.json()["total_assets"] == 0
            other_folders_resp = await other_client.get("/media/folders")
            assert len(other_folders_resp.json()) == 0

            # Other user cannot delete this asset
            del_forbidden = await other_client.delete(f"/media/{asset_id}")
            assert del_forbidden.status_code == 404

        # 5. Delete asset
        del_resp = await client.delete(f"/media/{asset_id}")
        assert del_resp.status_code == 204

        # Verify deletion
        list_after = await client.get("/media")
        assert list_after.json()["total_assets"] == 0
