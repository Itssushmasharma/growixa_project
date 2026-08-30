import urllib.parse
from typing import Any

import httpx

from growixa_api.auth.oauth.base import OAuthConfigurationError, OAuthError, OAuthUserProfile
from growixa_api.config import get_settings

_KEYCLOAK_SCOPES = ["openid", "email", "profile"]


class KeycloakOAuthProvider:
    provider_name: str = "keycloak"

    def __init__(
        self,
        issuer_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.issuer_url = issuer_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._http_client = http_client

    @property
    def effective_issuer_url(self) -> str:
        url = (self.issuer_url or get_settings().iam_oidc_issuer).rstrip("/")
        return url

    @property
    def effective_client_id(self) -> str:
        return self.client_id or get_settings().iam_client_id

    @property
    def effective_client_secret(self) -> str:
        return self.client_secret or get_settings().iam_client_secret

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is not None:
            return self._http_client
        return httpx.AsyncClient(timeout=15.0)

    def get_authorize_url(
        self, state: str, redirect_uri: str, kc_idp_hint: str | None = None
    ) -> str:
        issuer = self.effective_issuer_url
        client_id = self.effective_client_id
        if not issuer or not client_id:
            raise OAuthConfigurationError("Keycloak OIDC issuer or client_id is not configured")

        auth_endpoint = f"{issuer}/protocol/openid-connect/auth"
        params: dict[str, str] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(_KEYCLOAK_SCOPES),
            "state": state,
        }
        if kc_idp_hint:
            params["kc_idp_hint"] = kc_idp_hint

        return f"{auth_endpoint}?{urllib.parse.urlencode(params)}"

    async def exchange_code_and_get_profile(self, code: str, redirect_uri: str) -> OAuthUserProfile:
        issuer = self.effective_issuer_url
        client_id = self.effective_client_id
        client_secret = self.effective_client_secret
        if not issuer or not client_id:
            raise OAuthConfigurationError("Keycloak OIDC issuer or client_id is not configured")

        token_endpoint = f"{issuer}/protocol/openid-connect/token"
        userinfo_endpoint = f"{issuer}/protocol/openid-connect/userinfo"

        client = self._get_client()
        should_close = self._http_client is None

        try:
            # 1. Exchange authorization code for tokens
            data: dict[str, str] = {
                "code": code,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            if client_secret:
                data["client_secret"] = client_secret

            token_response = await client.post(token_endpoint, data=data)

            if token_response.status_code != 200:
                err_text = token_response.text[:200]
                status_code = token_response.status_code
                raise OAuthError(f"Keycloak token exchange failed ({status_code}): {err_text}")

            token_data: dict[str, Any] = token_response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise OAuthError("Keycloak response did not contain an access_token")

            # 2. Fetch user profile from userinfo endpoint
            userinfo_response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                err_text = userinfo_response.text[:200]
                status_code = userinfo_response.status_code
                raise OAuthError(f"Failed to fetch Keycloak userinfo ({status_code}): {err_text}")

            userinfo: dict[str, Any] = userinfo_response.json()

            provider_user_id = userinfo.get("sub")
            email = userinfo.get("email")
            # Keycloak returns boolean email_verified; trust true or default to true for social
            email_verified = bool(userinfo.get("email_verified", True))
            name = userinfo.get("name") or userinfo.get("preferred_username")
            avatar_url = userinfo.get("picture")

            if not provider_user_id or not email:
                raise OAuthError("Keycloak profile missing required sub or email claims")

            return OAuthUserProfile(
                provider=self.provider_name,
                provider_user_id=str(provider_user_id),
                email=str(email),
                is_email_verified=email_verified,
                full_name=name,
                avatar_url=avatar_url,
            )
        finally:
            if should_close:
                await client.aclose()
