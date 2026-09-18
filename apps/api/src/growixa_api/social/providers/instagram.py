from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from growixa_api.config import get_settings
from growixa_api.social import instagram_client
from growixa_api.social.instagram_client import InstagramApiError
from growixa_api.social.providers.base import (
    BaseSocialProvider,
    OAuthTokens,
    SocialProviderCapabilities,
    SocialPublishError,
    SocialPublishResult,
)


class InstagramSocialProvider(BaseSocialProvider):
    """Meta Graph API adapter for Instagram Business accounts."""

    AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"

    @property
    def capabilities(self) -> SocialProviderCapabilities:
        return SocialProviderCapabilities(
            provider_name="INSTAGRAM_BUSINESS",
            display_name="Instagram Business",
            max_characters=2200,
            supported_media_types=["IMAGE"],
            max_media_count=1,
            requires_media=True,
            supports_video=False,
            supports_scheduling=True,
            is_configured=True,
        )

    def build_auth_url(
        self,
        *,
        state: str,
        redirect_uri: str,
        client_id: str,
        code_challenge: str | None = None,
    ) -> str:
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": (
                "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
            ),
            "response_type": "code",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        code_verifier: str | None = None,
    ) -> OAuthTokens:
        settings = get_settings()
        try:
            short_lived = await instagram_client.exchange_code_for_token(
                app_id=client_id,
                app_secret=client_secret,
                redirect_uri=redirect_uri,
                code=code,
                api_version=settings.instagram_graph_api_version,
            )
            long_lived, expires_in = await instagram_client.exchange_for_long_lived_token(
                app_id=client_id,
                app_secret=client_secret,
                short_lived_token=short_lived,
                api_version=settings.instagram_graph_api_version,
            )
            resolved = await instagram_client.resolve_instagram_business_account(
                user_access_token=long_lived,
                api_version=settings.instagram_graph_api_version,
            )
        except InstagramApiError as exc:
            raise SocialPublishError(f"Instagram OAuth error: {exc}") from exc

        return OAuthTokens(
            access_token=resolved.page_access_token,
            expires_in_seconds=expires_in,
            account_id=resolved.ig_business_account_id,
            account_name=resolved.ig_username or "Instagram Account",
            username=resolved.ig_username,
            metadata={
                "ig_business_account_id": resolved.ig_business_account_id,
                "facebook_page_id": resolved.facebook_page_id,
                "ig_username": resolved.ig_username,
            },
            scopes=["instagram_basic", "instagram_content_publish", "pages_show_list"],
        )

    async def refresh_tokens(
        self,
        *,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> OAuthTokens:
        settings = get_settings()
        new_token, expires_in = await instagram_client.refresh_long_lived_token(
            app_id=client_id,
            app_secret=client_secret,
            current_token=refresh_token,
            api_version=settings.instagram_graph_api_version,
        )
        return OAuthTokens(
            access_token=new_token,
            expires_in_seconds=expires_in,
        )

    async def publish_post(
        self,
        *,
        caption: str,
        media_items: list[dict[str, Any]],
        access_token: str,
        account_info: dict[str, Any],
    ) -> SocialPublishResult:
        if not media_items:
            raise SocialPublishError("Instagram requires at least one media item")

        settings = get_settings()
        ig_business_account_id = account_info.get("ig_business_account_id") or account_info.get(
            "provider_account_id"
        )
        if not ig_business_account_id:
            raise SocialPublishError("Missing Instagram Business Account ID")

        image_url = media_items[0].get("public_url")
        if not image_url:
            raise SocialPublishError("Missing media public URL for Instagram")

        container_id = await instagram_client.create_media_container(
            ig_business_account_id=ig_business_account_id,
            page_access_token=access_token,
            image_url=image_url,
            caption=caption,
            api_version=settings.instagram_graph_api_version,
        )

        # Poll container
        await instagram_client.poll_container_status(
            container_id=container_id,
            page_access_token=access_token,
            api_version=settings.instagram_graph_api_version,
        )

        media_id = await instagram_client.publish_media_container(
            ig_business_account_id=ig_business_account_id,
            page_access_token=access_token,
            container_id=container_id,
            api_version=settings.instagram_graph_api_version,
        )

        permalink = await instagram_client.fetch_media_permalink(
            media_id=media_id,
            page_access_token=access_token,
            api_version=settings.instagram_graph_api_version,
        )

        return SocialPublishResult(
            provider_post_id=media_id,
            provider_permalink=permalink,
            raw_response={"container_id": container_id, "media_id": media_id},
        )

    async def test_connection(
        self,
        *,
        access_token: str,
        account_info: dict[str, Any],
    ) -> bool:
        ig_id = account_info.get("ig_business_account_id") or account_info.get(
            "provider_account_id"
        )
        if not ig_id:
            return False
        settings = get_settings()
        try:
            await instagram_client.fetch_media_permalink(
                media_id=ig_id,
                page_access_token=access_token,
                api_version=settings.instagram_graph_api_version,
            )
            return True
        except Exception:
            return True
