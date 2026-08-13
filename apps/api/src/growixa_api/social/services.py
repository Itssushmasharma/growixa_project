import secrets
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.billing.services import check_plan_limit
from growixa_api.config import get_settings
from growixa_api.files import storage_client
from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import JobEnvelope
from growixa_api.social import instagram_client, repositories, scheduler
from growixa_api.social.models import SocialConnection, SocialPost, SocialPostMedia
from growixa_api.social.schemas import ScheduleSocialPostIn, SocialPostIn, SocialPostUpdateIn

_PROVIDER = "INSTAGRAM_BUSINESS"
_STATE_KEY_PREFIX = "grx:social:instagram:oauth_state:"
# Per DEC-GRX-023's media-scope decision: a single JPEG image, ≤8MB, per post this slice.
_MAX_MEDIA_BYTES = 8 * 1024 * 1024
# Fire-once, no retry/DLQ -- mirrors email_delivery's SEND_CAMPAIGN_QUEUE exactly: a
# failure surfaces immediately via last_error/FAILED, retriable through GRX-SOCIAL-007's
# explicit /retry route rather than an automatic requeue.
PUBLISH_NOW_QUEUE = "grx.social.publish_now"
_JPEG_MAGIC_BYTES = b"\xff\xd8\xff"
# Verify against Meta's current dialog scopes at live-verification time (GRX-SOCIAL-008)
# — these drift across Graph API versions.
_OAUTH_SCOPES = (
    "instagram_basic",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
    "business_management",
)


class OAuthStateInvalidError(Exception):
    """The `state` param is missing, expired, unknown, or doesn't match the account that
    initiated the flow (THREAT_MODEL.md T44)."""


def _redirect_uri() -> str:
    return f"{get_settings().api_public_url}/integrations/instagram/oauth/callback"


async def build_authorize_url(redis_client: Redis, account_id: uuid.UUID) -> str:
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    await redis_client.set(
        f"{_STATE_KEY_PREFIX}{state}",
        str(account_id),
        ex=settings.instagram_oauth_state_ttl_seconds,
    )
    params = {
        "client_id": settings.instagram_app_id,
        "redirect_uri": _redirect_uri(),
        "state": state,
        "scope": ",".join(_OAUTH_SCOPES),
        "response_type": "code",
    }
    return (
        f"https://www.facebook.com/{settings.instagram_graph_api_version}/dialog/oauth"
        f"?{urlencode(params)}"
    )


async def complete_oauth_callback(
    session: AsyncSession,
    redis_client: Redis,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    code: str,
    state: str,
) -> SocialConnection:
    """Validates `state`, exchanges the code, resolves the linked Instagram Business
    Account, and persists the connection.

    Raises OAuthStateInvalidError or an `instagram_client.InstagramApiError` (including
    its `NoLinkedInstagramAccountError` subclass) on failure — the route layer maps both
    to a redirect back to the frontend, never a raw 500 (a browser lands here directly
    off Meta's own redirect).
    """
    state_key = f"{_STATE_KEY_PREFIX}{state}"
    stored_account_id = await redis_client.get(state_key)
    await redis_client.delete(state_key)  # single-use regardless of outcome
    if stored_account_id is None or stored_account_id != str(account_id):
        raise OAuthStateInvalidError("OAuth state is missing, expired, or mismatched")

    settings = get_settings()
    short_lived_token = await instagram_client.exchange_code_for_token(
        app_id=settings.instagram_app_id,
        app_secret=settings.instagram_app_secret,
        redirect_uri=_redirect_uri(),
        code=code,
        api_version=settings.instagram_graph_api_version,
    )
    long_lived_token, expires_in = await instagram_client.exchange_for_long_lived_token(
        app_id=settings.instagram_app_id,
        app_secret=settings.instagram_app_secret,
        short_lived_token=short_lived_token,
        api_version=settings.instagram_graph_api_version,
    )
    resolved = await instagram_client.resolve_instagram_business_account(
        user_access_token=long_lived_token,
        api_version=settings.instagram_graph_api_version,
    )

    # Only a genuinely new platform connection counts against the cap -- reconnecting an
    # already-connected provider deactivates-then-recreates (one active row per provider,
    # DEC-GRX-025) so it must not double-count. Reflects only *this* provider's active row
    # in the "would-be total after this operation" instead of the current total, so
    # reconnecting at the cap never spuriously blocks a refresh.
    existing_connection = await repositories.get_active_connection(session, account_id, _PROVIDER)
    if existing_connection is None:
        current_count = await repositories.count_active_connections(session, account_id)
        await check_plan_limit(
            session,
            account_id=account_id,
            limit_attr="max_social_accounts",
            current_count=current_count,
            resource="social_accounts",
        )

    await repositories.deactivate_active_connections(session, account_id, _PROVIDER)
    connection = await repositories.create_connection(
        session,
        {
            "account_id": account_id,
            "provider": _PROVIDER,
            "ig_business_account_id": resolved.ig_business_account_id,
            "ig_username": resolved.ig_username,
            "facebook_page_id": resolved.facebook_page_id,
            "access_token_encrypted": encrypt_secret(resolved.page_access_token),
            "token_expires_at": datetime.now(UTC) + timedelta(seconds=expires_in),
            "created_by_user_id": actor_id,
        },
    )
    await session.commit()
    return connection


class SocialConnectionNotFoundError(Exception):
    pass


class SocialPostNotFoundError(Exception):
    pass


class SocialPostMediaNotFoundError(Exception):
    pass


class SocialPostNotEditableError(Exception):
    """Raised when attempting to edit a post (or its media) whose status has left
    DRAFT — draft content is only mutable up until publishing starts, matching
    campaigns.services's CampaignNotEditableError."""


class InvalidMediaTypeError(Exception):
    pass


class MediaTooLargeError(Exception):
    pass


class TooManyMediaItemsError(Exception):
    pass


async def list_all_connections(
    session: AsyncSession, account_id: uuid.UUID
) -> Sequence[SocialConnection]:
    return await repositories.list_connections(session, account_id)


async def create_post(
    session: AsyncSession, account_id: uuid.UUID, data: SocialPostIn, actor_id: uuid.UUID
) -> SocialPost:
    connection = await repositories.get_connection(session, account_id, data.social_connection_id)
    if connection is None:
        raise SocialConnectionNotFoundError
    post = await repositories.create_post(
        session,
        {
            "account_id": account_id,
            "social_connection_id": data.social_connection_id,
            "caption": data.caption,
            "created_by_user_id": actor_id,
        },
    )
    await session.commit()
    await session.refresh(post)
    return post


async def get_post_or_raise(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID
) -> SocialPost:
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    return post


async def list_all_posts(session: AsyncSession, account_id: uuid.UUID) -> Sequence[SocialPost]:
    return await repositories.list_posts(session, account_id)


async def list_media_for_post(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID
) -> Sequence[SocialPostMedia]:
    return await repositories.list_post_media(session, account_id, post_id)


async def update_post(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID, data: SocialPostUpdateIn
) -> SocialPost:
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status != "DRAFT":
        raise SocialPostNotEditableError

    fields = data.model_dump(exclude_unset=True)
    post = await repositories.update_post_fields(session, post, fields)
    await session.commit()
    # updated_at's server-side onupdate expires the attribute after an UPDATE commit;
    # refresh explicitly while still inside an awaited call (see contacts/services.py).
    await session.refresh(post)
    return post


async def add_media(
    session: AsyncSession,
    account_id: uuid.UUID,
    post_id: uuid.UUID,
    *,
    content: bytes,
    content_type: str,
) -> SocialPostMedia:
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status != "DRAFT":
        raise SocialPostNotEditableError

    if content_type != "image/jpeg" or not content.startswith(_JPEG_MAGIC_BYTES):
        raise InvalidMediaTypeError("Only JPEG images are supported")
    if len(content) > _MAX_MEDIA_BYTES:
        raise MediaTooLargeError(f"Image must be {_MAX_MEDIA_BYTES // (1024 * 1024)}MB or smaller")

    existing = await repositories.list_post_media(session, account_id, post_id)
    if len(existing) >= 1:
        raise TooManyMediaItemsError("A post may have at most one media item this slice")

    settings = get_settings()
    storage_path = f"{account_id}/{post_id}/{uuid.uuid4()}.jpg"
    public_url = await storage_client.upload_object(
        storage_url=settings.supabase_storage_url,
        service_key=settings.supabase_storage_service_key,
        bucket=settings.supabase_storage_bucket,
        path=storage_path,
        content=content,
        content_type=content_type,
    )
    media = await repositories.create_post_media(
        session,
        {
            "account_id": account_id,
            "social_post_id": post_id,
            "media_type": "IMAGE",
            "storage_path": storage_path,
            "public_url": public_url,
            "position": len(existing),
        },
    )
    await session.commit()
    return media


async def remove_media(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID, media_id: uuid.UUID
) -> None:
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status != "DRAFT":
        raise SocialPostNotEditableError
    media = await repositories.get_post_media(session, account_id, post_id, media_id)
    if media is None:
        raise SocialPostMediaNotFoundError

    # Delete from storage before the DB row -- a failure here leaves both sides
    # consistent (row and file both still exist); deleting the row first could leave an
    # orphaned file with nothing pointing to it. StorageError propagates as-is; the API
    # layer maps it to a 502.
    settings = get_settings()
    await storage_client.delete_object(
        storage_url=settings.supabase_storage_url,
        service_key=settings.supabase_storage_service_key,
        bucket=settings.supabase_storage_bucket,
        path=media.storage_path,
    )

    await repositories.delete_post_media(session, media)
    await session.commit()


class PostHasNoMediaError(Exception):
    """Instagram's Content Publishing API has no text-only posts (DEC-GRX-023) —
    publishing or scheduling a post with zero media items is rejected here, not left
    for the worker to discover."""


class PostNotPublishableError(Exception):
    """Raised when publish-now is attempted against a post that isn't (or is no longer)
    a DRAFT — publishing twice, or publishing mid-publish, is not allowed. Mirrors
    email_delivery's CampaignNotSendableError."""


async def publish_now(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID, actor_id: uuid.UUID
) -> JobEnvelope:
    """Flips the post to DISPATCHING and enqueues the real publish as a worker job —
    never calls the Instagram API inline in this request, matching
    email_delivery.trigger_campaign_send's shape exactly."""
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status != "DRAFT":
        raise PostNotPublishableError
    media = await repositories.list_post_media(session, account_id, post_id)
    if len(media) == 0:
        raise PostHasNoMediaError

    post.status = "DISPATCHING"
    await session.commit()

    envelope = JobEnvelope(
        idempotency_key=f"social-post-publish-{post.id}",
        job_type=PUBLISH_NOW_QUEUE,
        payload={"social_post_id": str(post.id)},
        created_by_user_id=actor_id,
    )
    await publish_job(PUBLISH_NOW_QUEUE, envelope)
    return envelope


class PostAlreadyScheduledError(Exception):
    """Raised when scheduling a post that is not in DRAFT status. Mirrors
    campaigns.services's CampaignAlreadyScheduledError."""


class PostNotCancellableError(Exception):
    """Raised when cancelling a post that is not in DRAFT or SCHEDULED status. Mirrors
    campaigns.services's CampaignNotCancellableError."""


class PostNotRetryableError(Exception):
    """Raised when retrying a post that is not in FAILED status."""


async def schedule_post(
    session: AsyncSession,
    account_id: uuid.UUID,
    post_id: uuid.UUID,
    data: ScheduleSocialPostIn,
) -> SocialPost:
    """Move a DRAFT post to SCHEDULED status. Only DRAFT posts may be scheduled;
    `data.scheduled_at` must be strictly in the future (UTC). Mirrors
    campaigns.services.schedule_campaign exactly, plus the same has-media check
    publish_now enforces (Instagram has no text-only posts)."""
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status != "DRAFT":
        raise PostAlreadyScheduledError(
            f"Post is in status '{post.status}' and cannot be scheduled"
        )
    if data.scheduled_at.astimezone(UTC) <= datetime.now(UTC):
        raise ValueError("scheduled_at must be a future datetime")
    media = await repositories.list_post_media(session, account_id, post_id)
    if len(media) == 0:
        raise PostHasNoMediaError

    post = await repositories.update_post_fields(
        session, post, {"status": "SCHEDULED", "scheduled_at": data.scheduled_at}
    )
    await session.commit()
    await session.refresh(post)
    return post


async def cancel_post(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID
) -> SocialPost:
    """Cancel a DRAFT or SCHEDULED post before it is dispatched. Mirrors
    campaigns.services.cancel_campaign exactly."""
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status not in {"DRAFT", "SCHEDULED"}:
        raise PostNotCancellableError(f"Post is in status '{post.status}' and cannot be cancelled")

    post = await repositories.update_post_fields(
        session, post, {"status": "CANCELLED", "cancelled_at": datetime.now(UTC)}
    )
    await session.commit()
    await session.refresh(post)
    return post


async def retry_post(
    session: AsyncSession, account_id: uuid.UUID, post_id: uuid.UUID
) -> JobEnvelope:
    """Re-dispatches a FAILED post through the scheduled-dispatch pipeline (not the
    fire-once publish-now queue), so it gets the worker's own retry/DLQ ladder for this
    fresh attempt. Reuses the post's own fixed `idempotency_key` -- safe because the
    worker's idempotency guard (a Redis 'done' marker set only after success, backed by
    a DB-level SocialPostVersion existence check) never marks a FAILED attempt as done,
    so a retry with the same key is never mistaken for an already-processed one."""
    post = await repositories.get_post(session, account_id, post_id)
    if post is None:
        raise SocialPostNotFoundError
    if post.status != "FAILED":
        raise PostNotRetryableError(f"Post is in status '{post.status}' and cannot be retried")

    post.status = "DISPATCHING"
    post.last_error = None
    await session.commit()

    envelope = JobEnvelope(
        idempotency_key=str(post.idempotency_key),
        job_type=scheduler.DISPATCH_QUEUE,
        payload={"social_post_id": str(post.id)},
    )
    await publish_job(scheduler.DISPATCH_QUEUE, envelope)
    return envelope
