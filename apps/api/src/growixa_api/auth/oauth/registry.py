from growixa_api.auth.oauth.base import OAuthError, OAuthProvider
from growixa_api.auth.oauth.google import GoogleOAuthProvider
from growixa_api.auth.oauth.keycloak import KeycloakOAuthProvider

_PROVIDERS: dict[str, OAuthProvider] = {
    "google": GoogleOAuthProvider(),
    "keycloak": KeycloakOAuthProvider(),
    "iam": KeycloakOAuthProvider(),
    "iitd": KeycloakOAuthProvider(),
}


def get_oauth_provider(provider_name: str) -> OAuthProvider:
    provider = _PROVIDERS.get(provider_name.lower())
    if provider is None:
        raise OAuthError(f"Unsupported OAuth provider: {provider_name}")
    return provider
