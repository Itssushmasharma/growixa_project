# ruff: noqa: E501

from __future__ import annotations

from typing import Any

from growixa_api.social.providers.base import (
    BaseSocialProvider,
    OAuthTokens,
    SocialProviderCapabilities,
    SocialPublishError,
    SocialPublishResult,
)


class FacebookPageSocialProvider(BaseSocialProvider):
    """Adapter stub for Facebook Pages via Meta Graph API."""

    @property
    def capabilities(self) -> SocialProviderCapabilities:
        return SocialProviderCapabilities(
            provider_name="FACEBOOK_PAGE",
            display_name="Facebook Page",
            max_characters=5000,
            supported_media_types=["IMAGE", "VIDEO"],
            max_media_count=10,
            requires_media=False,
            supports_video=True,
            supports_scheduling=True,
            is_configured=False,
            setup_guide="Requires Meta App Review for 'pages_manage_posts' and 'pages_read_engagement' permissions.",
        )

    def build_auth_url(
        self,
        *,
        state: str,
        redirect_uri: str,
        client_id: str,
        code_challenge: str | None = None,
    ) -> str:
        raise SocialPublishError(
            "Facebook Page integration requires app credentials configuration.", status_code=501
        )

    async def exchange_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        code_verifier: str | None = None,
    ) -> OAuthTokens:
        raise SocialPublishError(
            "Facebook Page OAuth not configured on this instance.", status_code=501
        )

    async def refresh_tokens(
        self,
        *,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> OAuthTokens:
        raise SocialPublishError("Facebook Page token refresh not configured.", status_code=501)

    async def publish_post(
        self,
        *,
        caption: str,
        media_items: list[dict[str, Any]],
        access_token: str,
        account_info: dict[str, Any],
    ) -> SocialPublishResult:
        raise SocialPublishError(
            "Facebook Page publishing is not configured. Please connect with approved Meta credentials.",
            status_code=501,
        )

    async def test_connection(
        self,
        *,
        access_token: str,
        account_info: dict[str, Any],
    ) -> bool:
        return False


class YouTubeSocialProvider(BaseSocialProvider):
    """Adapter stub for YouTube Community & Video Publishing via Google YouTube Data API v3."""

    @property
    def capabilities(self) -> SocialProviderCapabilities:
        return SocialProviderCapabilities(
            provider_name="YOUTUBE",
            display_name="YouTube",
            max_characters=5000,
            supported_media_types=["VIDEO"],
            max_media_count=1,
            requires_media=True,
            supports_video=True,
            supports_scheduling=True,
            is_configured=False,
            setup_guide="Requires Google Cloud Console OAuth 2.0 Client ID with YouTube Data API v3 enabled.",
        )

    def build_auth_url(
        self,
        *,
        state: str,
        redirect_uri: str,
        client_id: str,
        code_challenge: str | None = None,
    ) -> str:
        raise SocialPublishError(
            "YouTube integration requires Google Cloud OAuth credentials configuration.",
            status_code=501,
        )

    async def exchange_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        code_verifier: str | None = None,
    ) -> OAuthTokens:
        raise SocialPublishError("YouTube OAuth not configured on this instance.", status_code=501)

    async def refresh_tokens(
        self,
        *,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> OAuthTokens:
        raise SocialPublishError("YouTube token refresh not configured.", status_code=501)

    async def publish_post(
        self,
        *,
        caption: str,
        media_items: list[dict[str, Any]],
        access_token: str,
        account_info: dict[str, Any],
    ) -> SocialPublishResult:
        raise SocialPublishError(
            "YouTube publishing is not configured. Please configure Google Cloud OAuth client credentials.",
            status_code=501,
        )

    async def test_connection(
        self,
        *,
        access_token: str,
        account_info: dict[str, Any],
    ) -> bool:
        return False
