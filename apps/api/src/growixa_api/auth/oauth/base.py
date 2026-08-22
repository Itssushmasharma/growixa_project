from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OAuthUserProfile:
    provider: str
    provider_user_id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    is_email_verified: bool = True


class OAuthError(Exception):
    """Generic OAuth error."""


class OAuthConfigurationError(OAuthError):
    """Missing or invalid client credentials for the OAuth provider."""


class OAuthProvider(Protocol):
    provider_name: str

    def get_authorize_url(self, state: str, redirect_uri: str) -> str:
        """Returns the provider consent URL."""
        ...

    async def exchange_code_and_get_profile(self, code: str, redirect_uri: str) -> OAuthUserProfile:
        """Exchanges auth code for access token and retrieves the normalized user profile."""
        ...
