import urllib.parse

import httpx

from growixa_api.auth.oauth.base import OAuthConfigurationError, OAuthError, OAuthUserProfile
from growixa_api.config import get_settings

_GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
_GOOGLE_SCOPES = ["openid", "email", "profile"]


class GoogleOAuthProvider:
    provider_name: str = "google"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._http_client = http_client

    @property
    def effective_client_id(self) -> str:
        return self.client_id or get_settings().google_client_id

    @property
    def effective_client_secret(self) -> str:
        return self.client_secret or get_settings().google_client_secret

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is not None:
            return self._http_client
        return httpx.AsyncClient(timeout=10.0)

    def get_authorize_url(
        self, state: str, redirect_uri: str, kc_idp_hint: str | None = None
    ) -> str:
        client_id = self.effective_client_id
        if not client_id:
            raise OAuthConfigurationError("Google OAuth client_id is not configured")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(_GOOGLE_SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{_GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"

    async def exchange_code_and_get_profile(self, code: str, redirect_uri: str) -> OAuthUserProfile:
        client_id = self.effective_client_id
        client_secret = self.effective_client_secret
        if not client_id or not client_secret:
            raise OAuthConfigurationError("Google OAuth credentials are not configured")

        client = self._get_client()
        should_close = self._http_client is None

        try:
            # 1. Exchange authorization code for tokens
            token_response = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )

            if token_response.status_code != 200:
                raise OAuthError(
                    f"Google token exchange failed with status {token_response.status_code}"
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise OAuthError("Google token response missing access_token")

            # 2. Fetch user profile via OpenID userinfo endpoint
            userinfo_response = await client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_response.status_code != 200:
                raise OAuthError(
                    f"Google userinfo request failed with status {userinfo_response.status_code}"
                )

            user_data = userinfo_response.json()
            provider_user_id = user_data.get("sub")
            email = user_data.get("email")

            if not provider_user_id or not email:
                raise OAuthError("Google user profile missing sub or email")

            # Google accounts report email_verified as a boolean
            is_email_verified = bool(user_data.get("email_verified", True))

            return OAuthUserProfile(
                provider=self.provider_name,
                provider_user_id=str(provider_user_id),
                email=str(email).strip().lower(),
                full_name=user_data.get("name"),
                avatar_url=user_data.get("picture"),
                is_email_verified=is_email_verified,
            )
        finally:
            if should_close:
                await client.aclose()
