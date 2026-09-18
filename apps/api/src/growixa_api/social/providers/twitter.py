from __future__ import annotations

import base64
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


class TwitterSocialProvider(BaseSocialProvider):
    """Official Twitter / X API v2 adapter."""

    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    USERS_ME_URL = "https://api.twitter.com/2/users/me"
    TWEETS_URL = "https://api.twitter.com/2/tweets"

    @property
    def capabilities(self) -> SocialProviderCapabilities:
        return SocialProviderCapabilities(
            provider_name="TWITTER",
            display_name="X / Twitter",
            max_characters=280,
            supported_media_types=["IMAGE", "VIDEO"],
            max_media_count=4,
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
            "scope": "tweet.read tweet.write users.read offline.access",
            "state": state,
            "code_challenge": code_challenge or "challenge",
            "code_challenge_method": "plain" if not code_challenge else "S256",
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
            "code": code,
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier or "challenge",
        }
        # Basic auth with client credentials
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(self.TOKEN_URL, data=data, headers=headers)
            if token_resp.is_error:
                raise SocialPublishError(
                    f"Twitter token exchange failed ({token_resp.status_code}): {token_resp.text}",
                    status_code=token_resp.status_code,
                )
            token_data = token_resp.json()
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 7200)

            # Fetch authenticated user profile
            user_resp = await client.get(
                self.USERS_ME_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"user.fields": "profile_image_url,username,name"},
            )
            user_dict = user_resp.json().get("data", {}) if user_resp.is_success else {}
            twitter_user_id = user_dict.get("id", "twitter_user")
            username = user_dict.get("username", "twitter_user")
            name = user_dict.get("name", username)

            return OAuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in_seconds=expires_in,
                account_id=str(twitter_user_id),
                account_name=name,
                username=username,
                metadata={
                    "twitter_id": twitter_user_id,
                    "profile_image_url": user_dict.get("profile_image_url"),
                },
                scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
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
        }
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_header}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.TOKEN_URL, data=data, headers=headers)
            if resp.is_error:
                raise SocialPublishError(
                    f"Twitter token refresh failed: {resp.text}",
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
        payload: dict[str, Any] = {"text": caption}

        async with httpx.AsyncClient(timeout=20.0) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            resp = await client.post(self.TWEETS_URL, json=payload, headers=headers)
            if resp.status_code == 429:
                raise SocialPublishError(
                    "Twitter/X API rate limit exceeded", status_code=429, is_retryable=True
                )
            if resp.is_error:
                raise SocialPublishError(
                    f"Twitter publish error ({resp.status_code}): {resp.text}",
                    status_code=resp.status_code,
                )
            tweet_data = resp.json().get("data", {})
            tweet_id = tweet_data.get("id", "tweet_id")
            username = account_info.get("provider_username") or "i"
            permalink = f"https://x.com/{username}/status/{tweet_id}"

            return SocialPublishResult(
                provider_post_id=str(tweet_id),
                provider_permalink=permalink,
                raw_response=resp.json(),
            )

    async def test_connection(
        self,
        *,
        access_token: str,
        account_info: dict[str, Any],
    ) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self.USERS_ME_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return resp.is_success
