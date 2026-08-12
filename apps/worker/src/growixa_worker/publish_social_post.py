import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker import instagram_client
from growixa_worker.config import get_settings
from growixa_worker.encryption import decrypt_secret, encrypt_secret
from growixa_worker.instagram_client import InstagramPublishError, TransientPublishError
from growixa_worker.models import SocialConnection, SocialPost, SocialPostMedia, SocialPostVersion

logger = logging.getLogger("growixa_worker")

# ~31s total budget across 5 polls -- a starting point; needs live verification against
# a real IG sandbox account before this task is marked DONE, per SPRINT_06's own note
# (container-processing time can't be pinned from docs alone).
_POLL_BACKOFF_SECONDS = [1, 2, 4, 8, 16]
# Refresh the Page access token if it expires within a week -- simplest correct
# approach for MVP (a proactive daily ticker is a reasonable future upgrade if
# scheduled-far-in-advance posts start hitting dead tokens in practice).
_TOKEN_REFRESH_THRESHOLD = timedelta(days=7)


async def handle_publish_social_post(session: AsyncSession, payload: dict[str, Any]) -> None:
    """Publishes one social post to Instagram: create container, poll until processed,
    publish, record an immutable SocialPostVersion snapshot.

    Idempotency: a SocialPostVersion already existing for this post is the authoritative
    "already published" signal (mirrors handle_send_campaign/CampaignVersion exactly) --
    checked first, before any Graph API call.

    Does not catch InstagramPublishError (or anything else) -- that's the caller's job
    (consumer.py), which needs to distinguish PermanentPublishError (skip the retry
    ladder, straight to FAILED/DLQ) from a transient failure (retry) and, for the
    fire-once publish-now path, simply mark FAILED with no retry at all.
    """
    post_id = payload["social_post_id"]
    post = await session.get(SocialPost, post_id)
    if post is None:
        logger.error("publish_social_post: post %s not found, dropping job", post_id)
        return

    already_published = await session.execute(
        select(SocialPostVersion.id).where(SocialPostVersion.social_post_id == post.id).limit(1)
    )
    if already_published.scalar_one_or_none() is not None:
        logger.info("publish_social_post: post %s already has a snapshot, no-op", post_id)
        return

    connection = await session.get(SocialConnection, post.social_connection_id)
    if connection is None:
        raise TransientPublishError(f"post {post_id} has no resolvable social connection")

    media_result = await session.execute(
        select(SocialPostMedia)
        .where(SocialPostMedia.social_post_id == post.id)
        .order_by(SocialPostMedia.position)
    )
    media_items = media_result.scalars().all()
    if not media_items:
        raise InstagramPublishError(f"post {post_id} has no media to publish")

    settings = get_settings()
    access_token = decrypt_secret(connection.access_token_encrypted)

    if (
        connection.token_expires_at is not None
        and connection.token_expires_at - datetime.now(UTC) < _TOKEN_REFRESH_THRESHOLD
    ):
        new_token, expires_in = await instagram_client.refresh_long_lived_token(
            app_id=settings.instagram_app_id,
            app_secret=settings.instagram_app_secret,
            current_token=access_token,
            api_version=settings.instagram_graph_api_version,
        )
        access_token = new_token
        connection.access_token_encrypted = encrypt_secret(new_token)
        connection.token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        await session.flush()

    media = media_items[0]
    container_id = await instagram_client.create_media_container(
        ig_business_account_id=connection.ig_business_account_id,
        page_access_token=access_token,
        image_url=media.public_url,
        caption=post.caption,
        api_version=settings.instagram_graph_api_version,
    )

    for delay in _POLL_BACKOFF_SECONDS:
        status_code = await instagram_client.poll_container_status(
            container_id=container_id,
            page_access_token=access_token,
            api_version=settings.instagram_graph_api_version,
        )
        if status_code == "FINISHED":
            break
        if status_code in ("ERROR", "EXPIRED"):
            raise TransientPublishError(f"container {container_id} ended in status {status_code}")
        await asyncio.sleep(delay)
    else:
        raise TransientPublishError(f"container {container_id} did not finish processing in time")

    media_id = await instagram_client.publish_container(
        ig_business_account_id=connection.ig_business_account_id,
        container_id=container_id,
        page_access_token=access_token,
        api_version=settings.instagram_graph_api_version,
    )
    permalink = await instagram_client.fetch_permalink(
        media_id=media_id,
        page_access_token=access_token,
        api_version=settings.instagram_graph_api_version,
    )

    session.add(
        SocialPostVersion(
            account_id=post.account_id,
            social_post_id=post.id,
            caption=post.caption,
            media_snapshot=[
                {
                    "storage_path": item.storage_path,
                    "public_url": item.public_url,
                    "media_type": item.media_type,
                }
                for item in media_items
            ],
            ig_media_id=media_id,
        )
    )
    post.status = "PUBLISHED"
    post.published_at = datetime.now(UTC)
    post.ig_media_id = media_id
    post.ig_permalink = permalink
    post.last_error = None
    await session.commit()
    logger.info("publish_social_post: post %s published as %s", post_id, media_id)
