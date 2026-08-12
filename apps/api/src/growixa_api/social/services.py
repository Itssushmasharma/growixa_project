import secrets
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.config import get_settings
from growixa_api.files import storage_client
from growixa_api.social import instagram_client, repositories
from growixa_api.social.models import SocialConnection, SocialPost, SocialPostMedia
from growixa_api.social.schemas import SocialPostIn, SocialPostUpdateIn

_PROVIDER = "INSTAGRAM_BUSINESS"
_STATE_KEY_PREFIX = "grx:social:instagram:oauth_state:"
# Per DEC-GRX-023's media-scope decision: a single JPEG image, ≤8MB, per post this slice.
_MAX_MEDIA_BYTES = 8 * 1024 * 1024
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
