import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker import instagram_client as instagram_client
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
    """Publishes one social post across configured channels (Instagram, Twitter/X, LinkedIn):
    records an immutable SocialPostVersion snapshot upon success.

    Idempotency: a SocialPostVersion already existing for this post is the authoritative
    "already published" signal -- checked first, before any external API call.
    """
    post_id = payload["social_post_id"]
    post = await session.get(SocialPost, post_id)
    if post is None:
        logger.error("publish_social_post: post %s not found, dropping job", post_id)
        return

    # Enforce Approval State Machine (Phase A)
    if post.status not in ("APPROVED", "SCHEDULED", "DISPATCHING", "PUBLISHING"):
        raise TransientPublishError(f"post {post_id} is in status {post.status}, not APPROVED, SCHEDULED, DISPATCHING or PUBLISHING")

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
    media_items = list(media_result.scalars().all())

    provider = (connection.provider or "INSTAGRAM_BUSINESS").upper()
    if not media_items and provider == "INSTAGRAM_BUSINESS":
        raise InstagramPublishError(f"post {post_id} has no media to publish")

    access_token = decrypt_secret(connection.access_token_encrypted)

    if provider == "TWITTER":
        # Official Twitter/X API v2 Publish
        tweet_payload = {"text": post.caption}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.twitter.com/2/tweets",
                json=tweet_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code == 429:
                raise TransientPublishError("Twitter API rate limit exceeded")
            if resp.is_error:
                raise InstagramPublishError(
                    f"Twitter publish error ({resp.status_code}): {resp.text}"
                )
            tweet_data = resp.json().get("data", {})
            provider_post_id = str(tweet_data.get("id", "tweet_id"))
            username = connection.provider_username or "i"
            permalink = f"https://x.com/{username}/status/{provider_post_id}"

    elif provider == "LINKEDIN":
        # Official LinkedIn Community Management UGC Post API
        author_urn = connection.provider_account_id or "urn:li:person:self"
        share_media = []
        for item in media_items:
            if item.public_url:
                share_media.append(
                    {
                        "status": "READY",
                        "originalUrl": item.public_url,
                        "description": {"text": post.caption[:200]},
                        "title": {"text": "Media Attachment"},
                    }
                )

        share_content: dict[str, Any] = {
            "shareCommentary": {"text": post.caption},
            "shareMediaCategory": "IMAGE" if share_media else "NONE",
        }
        if share_media:
            share_content["media"] = share_media

        ugc_payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json",
            }
            resp = await client.post(
                "https://api.linkedin.com/v2/ugcPosts", json=ugc_payload, headers=headers
            )
            if resp.status_code == 429:
                raise TransientPublishError("LinkedIn API rate limit exceeded")
            if resp.is_error:
                raise InstagramPublishError(
                    f"LinkedIn publish error ({resp.status_code}): {resp.text}"
                )
            resp_data = resp.json()
            provider_post_id = resp_data.get("id") or resp.headers.get(
                "x-restli-id", "urn:li:share:published"
            )
            permalink = f"https://www.linkedin.com/feed/update/{provider_post_id}"

    else:
        # Instagram Business Publishing
        settings = get_settings()
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
                raise TransientPublishError(
                    f"container {container_id} ended in status {status_code}"
                )
            await asyncio.sleep(delay)
        else:
            raise TransientPublishError(
                f"container {container_id} did not finish processing in time"
            )

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
        provider_post_id = media_id

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
            ig_media_id=provider_post_id,
        )
    )
    post.status = "PUBLISHED"
    post.published_at = datetime.now(UTC)
    post.ig_media_id = provider_post_id
    post.ig_permalink = permalink
    post.provider_post_id = provider_post_id
    post.provider_permalink = permalink
    post.last_error = None
    await session.commit()
    logger.info(
        "publish_social_post: post %s published as %s to %s", post_id, provider_post_id, provider
    )
