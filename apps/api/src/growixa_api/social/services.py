import secrets
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.encryption import encrypt_secret
from growixa_api.config import get_settings
from growixa_api.social import instagram_client, repositories
from growixa_api.social.models import SocialConnection

_PROVIDER = "INSTAGRAM_BUSINESS"
_STATE_KEY_PREFIX = "grx:social:instagram:oauth_state:"
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
