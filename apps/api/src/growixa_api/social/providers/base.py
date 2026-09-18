# ruff: noqa: E501

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SocialProviderCapabilities:
    provider_name: str
    display_name: str
    max_characters: int
    supported_media_types: list[str] = field(default_factory=lambda: ["IMAGE"])
    max_media_count: int = 1
    requires_media: bool = False
    supports_video: bool = False
    supports_scheduling: bool = True
    is_configured: bool = True
    setup_guide: str | None = None


@dataclass
class SocialPublishResult:
    provider_post_id: str
    provider_permalink: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class OAuthTokens:
    access_token: str
    refresh_token: str | None = None
    expires_in_seconds: int | None = None
    account_id: str = ""
    account_name: str = ""
    username: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    scopes: list[str] = field(default_factory=list)


class SocialPublishError(Exception):
    """Base exception for social publishing errors."""

    def __init__(self, message: str, status_code: int = 400, is_retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_retryable = is_retryable


class BaseSocialProvider(abc.ABC):
    """Abstract base class for all social network provider adapters."""

    @property
    @abc.abstractmethod
    def capabilities(self) -> SocialProviderCapabilities:
        raise NotImplementedError

    @abc.abstractmethod
    def build_auth_url(
        self,
        *,
        state: str,
        redirect_uri: str,
        client_id: str,
        code_challenge: str | None = None,
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def exchange_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        code_verifier: str | None = None,
    ) -> OAuthTokens:
        raise NotImplementedError

    @abc.abstractmethod
    async def refresh_tokens(
        self,
        *,
        refresh_token: str,
        client_id: str,
        client_secret: str,
    ) -> OAuthTokens:
        raise NotImplementedError

    def validate_post(self, caption: str, media_items: list[dict[str, Any]]) -> list[str]:
        """Validates post content and media against this provider's official capabilities.
        Returns a list of validation error strings, or an empty list if valid."""
        errors: list[str] = []
        caps = self.capabilities

        if len(caption) > caps.max_characters:
            errors.append(
                f"{caps.display_name} posts cannot exceed {caps.max_characters} characters (current: {len(caption)})."
            )

        if caps.requires_media and len(media_items) == 0:
            errors.append(f"{caps.display_name} requires at least one media item to publish.")

        if len(media_items) > caps.max_media_count:
            errors.append(
                f"{caps.display_name} allows a maximum of {caps.max_media_count} media item(s) (provided: {len(media_items)})."
            )

        for item in media_items:
            media_type = item.get("media_type", "IMAGE")
            if media_type not in caps.supported_media_types:
                errors.append(f"{caps.display_name} does not support media type '{media_type}'.")

        return errors

    @abc.abstractmethod
    async def publish_post(
        self,
        *,
        caption: str,
        media_items: list[dict[str, Any]],
        access_token: str,
        account_info: dict[str, Any],
    ) -> SocialPublishResult:
        raise NotImplementedError

    @abc.abstractmethod
    async def test_connection(
        self,
        *,
        access_token: str,
        account_info: dict[str, Any],
    ) -> bool:
        raise NotImplementedError
