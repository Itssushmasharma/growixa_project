from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from growixa_api.social.providers.base import (
    BaseSocialProvider,
    OAuthTokens,
    SocialProviderCapabilities,
    SocialPublishError,
    SocialPublishResult,
)


class LinkedInSocialProvider(BaseSocialProvider):
    """Official LinkedIn Community Management and Share API adapter."""

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"

    @property
    def capabilities(self) -> SocialProviderCapabilities:
        return SocialProviderCapabilities(
            provider_name="LINKEDIN",
            display_name="LinkedIn",
            max_characters=3000,
            supported_media_types=["IMAGE", "VIDEO"],
            max_media_count=9,
            requires_media=False,
            supports_video=True,
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
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid profile email w_member_social",
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
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(self.TOKEN_URL, data=data)
            if token_resp.is_error:
                raise SocialPublishError(
                    f"LinkedIn token exchange failed ({token_resp.status_code}): {token_resp.text}",
                    status_code=token_resp.status_code,
                )
            token_data = token_resp.json()
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 5184000)

            # Fetch authenticated user profile
            profile_resp = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_data = profile_resp.json() if profile_resp.is_success else {}
            sub = profile_data.get("sub", "")
            name = profile_data.get("name") or profile_data.get("given_name", "LinkedIn Member")
            email = profile_data.get("email")

            return OAuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in_seconds=expires_in,
                account_id=f"urn:li:person:{sub}" if sub else "urn:li:person:unknown",
                account_name=name,
                username=email or name,
                metadata={
                    "sub": sub,
                    "picture": profile_data.get("picture"),
                    "email": email,
                },
                scopes=["openid", "profile", "email", "w_member_social"],
            )

    async def refresh_tokens(
        self,
        *,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> OAuthTokens:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.TOKEN_URL, data=data)
            if resp.is_error:
                raise SocialPublishError(
                    f"LinkedIn token refresh failed: {resp.text}",
                    status_code=resp.status_code,
                )
            token_data = resp.json()
            return OAuthTokens(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", refresh_token),
                expires_in_seconds=token_data.get("expires_in"),
            )

    async def publish_post(
        self,
        *,
        caption: str,
        media_items: list[dict[str, Any]],
        access_token: str,
        account_info: dict[str, Any],
    ) -> SocialPublishResult:
        author_urn = account_info.get("provider_account_id") or "urn:li:person:self"

        # Build LinkedIn UGC share body
        share_media: list[dict[str, Any]] = []
        for item in media_items:
            public_url = item.get("public_url")
            if public_url:
                share_media.append(
                    {
                        "status": "READY",
                        "originalUrl": public_url,
                        "description": {"text": caption[:200]},
                        "title": {"text": "Media Attachment"},
                    }
                )

        share_content: dict[str, Any] = {
            "shareCommentary": {"text": caption},
            "shareMediaCategory": "IMAGE" if share_media else "NONE",
        }
        if share_media:
            share_content["media"] = share_media

        payload = {
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
            resp = await client.post(self.UGC_POSTS_URL, json=payload, headers=headers)
            if resp.status_code == 429:
                raise SocialPublishError(
                    "LinkedIn API rate limit exceeded", status_code=429, is_retryable=True
                )
            if resp.is_error:
                raise SocialPublishError(
                    f"LinkedIn publish error ({resp.status_code}): {resp.text}",
                    status_code=resp.status_code,
                )
            resp_data = resp.json()
            post_urn = resp_data.get("id") or resp.headers.get(
                "x-restli-id", "urn:li:share:published"
            )
            permalink = f"https://www.linkedin.com/feed/update/{post_urn}"

            return SocialPublishResult(
                provider_post_id=post_urn,
                provider_permalink=permalink,
                raw_response=resp_data,
            )

    async def test_connection(
        self,
        *,
        access_token: str,
        account_info: dict[str, Any],
    ) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return resp.is_success
