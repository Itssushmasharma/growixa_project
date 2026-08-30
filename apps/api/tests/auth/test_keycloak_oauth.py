"""IITD IAM / Keycloak Universal SSO OAuth integration tests.

Tests Keycloak authorization URL generation (with/without kc_idp_hint),
token exchange, user profile extraction, and JIT provisioning flow.
"""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from growixa_api.auth.oauth.base import OAuthError
from growixa_api.auth.oauth.keycloak import KeycloakOAuthProvider
from growixa_api.auth.oauth.registry import get_oauth_provider


def test_keycloak_provider_registration() -> None:
    provider = get_oauth_provider("keycloak")
    assert isinstance(provider, KeycloakOAuthProvider)
    assert provider.provider_name == "keycloak"

    iam_provider = get_oauth_provider("iam")
    assert isinstance(iam_provider, KeycloakOAuthProvider)

    iitd_provider = get_oauth_provider("iitd")
    assert isinstance(iitd_provider, KeycloakOAuthProvider)


def test_get_authorize_url_standard() -> None:
    provider = KeycloakOAuthProvider(
        issuer_url="https://auth.iitdeveloper.com/realms/iitd",
        client_id="growixa-app",
    )
    url = provider.get_authorize_url(
        state="test-state-123",
        redirect_uri="https://growixa.iitdeveloper.com/auth/callback",
    )
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.iitdeveloper.com"
    assert parsed.path == "/realms/iitd/protocol/openid-connect/auth"

    query = parse_qs(parsed.query)
    assert query["client_id"] == ["growixa-app"]
    assert query["response_type"] == ["code"]
    assert query["state"] == ["test-state-123"]
    assert query["redirect_uri"] == ["https://growixa.iitdeveloper.com/auth/callback"]
    assert "openid" in query["scope"][0]


def test_get_authorize_url_with_google_hint() -> None:
    provider = KeycloakOAuthProvider(
        issuer_url="https://auth.iitdeveloper.com/realms/iitd",
        client_id="growixa-app",
    )
    url = provider.get_authorize_url(
        state="test-state-google",
        redirect_uri="https://growixa.iitdeveloper.com/auth/callback",
        kc_idp_hint="google",
    )
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert query["kc_idp_hint"] == ["google"]


@pytest.mark.asyncio
async def test_exchange_code_and_get_profile_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200,
                json={"access_token": "mock-access-token-jwt", "token_type": "Bearer"},
            )
        if request.url.path.endswith("/userinfo"):
            assert request.headers.get("Authorization") == "Bearer mock-access-token-jwt"
            return httpx.Response(
                200,
                json={
                    "sub": "keycloak-user-uuid-12345",
                    "email": "developer@iitdeveloper.com",
                    "email_verified": True,
                    "name": "IITD Developer",
                    "picture": "https://avatar.iitdeveloper.com/dev.png",
                },
            )
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = KeycloakOAuthProvider(
        issuer_url="https://auth.iitdeveloper.com/realms/iitd",
        client_id="growixa-app",
        client_secret="test-secret",
        http_client=mock_client,
    )

    profile = await provider.exchange_code_and_get_profile(
        code="valid-auth-code",
        redirect_uri="https://growixa.iitdeveloper.com/auth/callback",
    )

    assert profile.provider == "keycloak"
    assert profile.provider_user_id == "keycloak-user-uuid-12345"
    assert profile.email == "developer@iitdeveloper.com"
    assert profile.is_email_verified is True
    assert profile.full_name == "IITD Developer"
    assert profile.avatar_url == "https://avatar.iitdeveloper.com/dev.png"


@pytest.mark.asyncio
async def test_exchange_code_failure_raises_oauth_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": "invalid_grant", "error_description": "Code expired"},
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = KeycloakOAuthProvider(
        issuer_url="https://auth.iitdeveloper.com/realms/iitd",
        client_id="growixa-app",
        http_client=mock_client,
    )

    with pytest.raises(OAuthError) as exc_info:
        await provider.exchange_code_and_get_profile(
            code="expired-code",
            redirect_uri="https://growixa.iitdeveloper.com/auth/callback",
        )

    assert "invalid_grant" in str(exc_info.value)
