"""publish_social_post job handler integration tests (GRX-SOCIAL-008, worker side).

Integration-tier: exercises the real Postgres database growixa_api's migrations created
(apps/worker/.env points at the same Compose instance apps/api uses). The real Instagram
Graph API is monkeypatched — no live Meta Developer App available, same documented-
evidence-gap convention as test_send_campaign.py's monkeypatched SMTP transport.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker import publish_social_post as publish_social_post_module
from growixa_worker.config import get_settings
from growixa_worker.db import get_session_factory
from growixa_worker.encryption import decrypt_secret
from growixa_worker.instagram_client import PermanentPublishError, TransientPublishError
from growixa_worker.models import SocialConnection, SocialPost, SocialPostMedia, SocialPostVersion
from growixa_worker.publish_social_post import handle_publish_social_post

# The seed account every GRX-SAAS-001 migration backfills pre-existing data into --
# guaranteed to exist in any migrated DB, matching test_send_campaign.py's identical note.
_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _encrypt(plaintext: str) -> str:
    return Fernet(get_settings().encryption_key.encode()).encrypt(plaintext.encode()).decode()


@pytest.fixture(autouse=True)
async def cleanup() -> AsyncGenerator[None, None]:
    async with get_session_factory()() as session:
        await session.execute(delete(SocialPostVersion))
        await session.execute(delete(SocialPostMedia))
        await session.execute(delete(SocialPost))
        await session.execute(delete(SocialConnection))
        await session.commit()
    yield
    async with get_session_factory()() as session:
        await session.execute(delete(SocialPostVersion))
        await session.execute(delete(SocialPostMedia))
        await session.execute(delete(SocialPost))
        await session.execute(delete(SocialConnection))
        await session.commit()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


async def _create_connection(
    session: AsyncSession, *, token_expires_at: datetime | None = None
) -> uuid.UUID:
    connection = SocialConnection(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        provider="INSTAGRAM_BUSINESS",
        ig_business_account_id="ig-123",
        facebook_page_id="page-123",
        access_token_encrypted=_encrypt("fake-page-access-token"),
        token_expires_at=token_expires_at,
    )
    session.add(connection)
    await session.commit()
    return connection.id


async def _create_post_with_media(session: AsyncSession, connection_id: uuid.UUID) -> uuid.UUID:
    post = SocialPost(
        id=uuid.uuid4(),
        account_id=_ACCOUNT_ID,
        social_connection_id=connection_id,
        caption="Test caption",
        status="DISPATCHING",
    )
    session.add(post)
    await session.flush()
    session.add(
        SocialPostMedia(
            id=uuid.uuid4(),
            account_id=_ACCOUNT_ID,
            social_post_id=post.id,
            media_type="IMAGE",
            storage_path=f"{_ACCOUNT_ID}/{post.id}/test.jpg",
            public_url="https://fake-supabase.test/test.jpg",
            position=0,
        )
    )
    await session.commit()
    return post.id


async def _cleanup(session: AsyncSession) -> None:
    await session.execute(delete(SocialPostVersion))
    await session.execute(delete(SocialPostMedia))
    await session.execute(delete(SocialPost))
    await session.execute(delete(SocialConnection))
    await session.commit()


@pytest.mark.integration
async def test_successful_publish_creates_version_and_updates_post(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_create_container(**kwargs: object) -> str:
        return "container-123"

    async def _fake_poll_status(**kwargs: object) -> str:
        return "FINISHED"

    async def _fake_publish_container(**kwargs: object) -> str:
        return "media-456"

    async def _fake_fetch_permalink(**kwargs: object) -> str:
        return "https://instagram.com/p/abc123"

    monkeypatch.setattr(
        publish_social_post_module.instagram_client,
        "create_media_container",
        _fake_create_container,
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "poll_container_status", _fake_poll_status
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "publish_container", _fake_publish_container
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "fetch_permalink", _fake_fetch_permalink
    )

    try:
        connection_id = await _create_connection(session)
        post_id = await _create_post_with_media(session, connection_id)

        await handle_publish_social_post(session, {"social_post_id": str(post_id)})

        post = await session.get(SocialPost, post_id)
        assert post is not None
        assert post.status == "PUBLISHED"
        assert post.ig_media_id == "media-456"
        assert post.ig_permalink == "https://instagram.com/p/abc123"
        assert post.published_at is not None

        version_result = await session.execute(
            select(SocialPostVersion).where(SocialPostVersion.social_post_id == post_id)
        )
        version = version_result.scalar_one()
        assert version.ig_media_id == "media-456"
        assert len(version.media_snapshot) == 1
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_idempotency_noop_when_version_already_exists(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    call_count = 0

    async def _fake_create_container(**kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return "container-should-not-be-called"

    monkeypatch.setattr(
        publish_social_post_module.instagram_client,
        "create_media_container",
        _fake_create_container,
    )

    try:
        connection_id = await _create_connection(session)
        post_id = await _create_post_with_media(session, connection_id)
        session.add(
            SocialPostVersion(
                id=uuid.uuid4(),
                account_id=_ACCOUNT_ID,
                social_post_id=post_id,
                caption="Already published",
                media_snapshot=[],
                ig_media_id="already-there",
            )
        )
        await session.commit()

        await handle_publish_social_post(session, {"social_post_id": str(post_id)})

        assert call_count == 0
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_permanent_publish_error_propagates(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_create_container(**kwargs: object) -> str:
        raise PermanentPublishError("OAuthException: token expired")

    monkeypatch.setattr(
        publish_social_post_module.instagram_client,
        "create_media_container",
        _fake_create_container,
    )

    try:
        connection_id = await _create_connection(session)
        post_id = await _create_post_with_media(session, connection_id)

        with pytest.raises(PermanentPublishError):
            await handle_publish_social_post(session, {"social_post_id": str(post_id)})

        # handle_publish_social_post never marks the post itself -- that's consumer.py's
        # job, since it needs to distinguish permanent from transient before deciding.
        post = await session.get(SocialPost, post_id)
        assert post is not None
        assert post.status == "DISPATCHING"
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_transient_publish_error_propagates(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_create_container(**kwargs: object) -> str:
        raise TransientPublishError("rate limited")

    monkeypatch.setattr(
        publish_social_post_module.instagram_client,
        "create_media_container",
        _fake_create_container,
    )

    try:
        connection_id = await _create_connection(session)
        post_id = await _create_post_with_media(session, connection_id)

        with pytest.raises(TransientPublishError):
            await handle_publish_social_post(session, {"social_post_id": str(post_id)})
    finally:
        await _cleanup(session)


@pytest.mark.integration
async def test_near_expiry_token_is_refreshed_before_publishing(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    refresh_calls: list[str] = []

    async def _fake_refresh(**kwargs: object) -> tuple[str, int]:
        refresh_calls.append(str(kwargs["current_token"]))
        return "refreshed-token", 5184000

    async def _fake_create_container(**kwargs: object) -> str:
        assert kwargs["page_access_token"] == "refreshed-token"
        return "container-123"

    async def _fake_poll_status(**kwargs: object) -> str:
        return "FINISHED"

    async def _fake_publish_container(**kwargs: object) -> str:
        return "media-456"

    async def _fake_fetch_permalink(**kwargs: object) -> str | None:
        return None

    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "refresh_long_lived_token", _fake_refresh
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client,
        "create_media_container",
        _fake_create_container,
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "poll_container_status", _fake_poll_status
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "publish_container", _fake_publish_container
    )
    monkeypatch.setattr(
        publish_social_post_module.instagram_client, "fetch_permalink", _fake_fetch_permalink
    )

    try:
        connection_id = await _create_connection(
            session, token_expires_at=datetime.now(UTC) + timedelta(days=1)
        )
        post_id = await _create_post_with_media(session, connection_id)

        await handle_publish_social_post(session, {"social_post_id": str(post_id)})

        assert refresh_calls == ["fake-page-access-token"]
        connection = await session.get(SocialConnection, connection_id)
        assert connection is not None
        assert decrypt_secret(connection.access_token_encrypted) == "refreshed-token"
    finally:
        await _cleanup(session)
