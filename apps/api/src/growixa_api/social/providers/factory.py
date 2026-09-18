from __future__ import annotations

from growixa_api.social.providers.base import BaseSocialProvider, SocialProviderCapabilities
from growixa_api.social.providers.instagram import InstagramSocialProvider
from growixa_api.social.providers.linkedin import LinkedInSocialProvider
from growixa_api.social.providers.stubs import FacebookPageSocialProvider, YouTubeSocialProvider
from growixa_api.social.providers.twitter import TwitterSocialProvider

_PROVIDERS: dict[str, BaseSocialProvider] = {
    "LINKEDIN": LinkedInSocialProvider(),
    "TWITTER": TwitterSocialProvider(),
    "INSTAGRAM_BUSINESS": InstagramSocialProvider(),
    "FACEBOOK_PAGE": FacebookPageSocialProvider(),
    "YOUTUBE": YouTubeSocialProvider(),
}


def get_social_provider(provider_name: str) -> BaseSocialProvider:
    """Returns the adapter instance for the given social provider name."""
    norm = (provider_name or "").upper().strip()
    if norm in _PROVIDERS:
        return _PROVIDERS[norm]
    raise ValueError(
        f"Unknown social provider: '{provider_name}'. Supported: {list(_PROVIDERS.keys())}"
    )


def list_available_channels() -> list[SocialProviderCapabilities]:
    """Returns capabilities for all supported and prepared social channels."""
    return [provider.capabilities for provider in _PROVIDERS.values()]
