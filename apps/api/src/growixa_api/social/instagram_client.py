from dataclasses import dataclass
from typing import Any

import httpx

_GRAPH_API_BASE = "https://graph.facebook.com"
_TIMEOUT_SECONDS = 15.0


class InstagramApiError(Exception):
    """Wraps any failure talking to the Meta Graph API (network, or a Graph-returned
    error payload) behind one type, mirroring smtp_transport.py's EmailSendError shape."""


@dataclass
class ResolvedInstagramAccount:
    facebook_page_id: str
    ig_business_account_id: str
    ig_username: str | None
    # The Page's own access token, not the user token — this is what's actually used to
    # publish through the linked Instagram Business Account. Derived from (and inherits
    # the long-lived status of) the long-lived user token exchanged just before it.
    page_access_token: str


def _extract_or_raise(response: httpx.Response) -> dict[str, Any]:
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        raise InstagramApiError(
            f"Non-JSON response from Graph API (HTTP {response.status_code})"
        ) from exc
    if "error" in data:
        error = data["error"]
        raise InstagramApiError(f"{error.get('type', 'GraphError')}: {error.get('message', data)}")
    if response.is_error:
        raise InstagramApiError(f"Graph API returned HTTP {response.status_code}: {data}")
    return data


async def exchange_code_for_token(
    *, app_id: str, app_secret: str, redirect_uri: str, code: str, api_version: str
) -> str:
    """Exchanges an OAuth authorization code for a short-lived user access token."""
    url = f"{_GRAPH_API_BASE}/{api_version}/oauth/access_token"
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise InstagramApiError(str(exc)) from exc
    data = _extract_or_raise(response)
    return str(data["access_token"])


async def exchange_for_long_lived_token(
    *, app_id: str, app_secret: str, short_lived_token: str, api_version: str
) -> tuple[str, int]:
    """Exchanges a short-lived user token for a long-lived one (~60 days).

    Returns (access_token, expires_in_seconds).
    """
    url = f"{_GRAPH_API_BASE}/{api_version}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise InstagramApiError(str(exc)) from exc
    data = _extract_or_raise(response)
    # 5184000s = 60 days is Meta's documented long-lived-token lifetime; used as a
    # fallback since expires_in is occasionally omitted for tokens that don't expire.
    return str(data["access_token"]), int(data.get("expires_in", 5184000))


async def resolve_instagram_business_account(
    *, user_access_token: str, api_version: str
) -> ResolvedInstagramAccount:
    """Finds the first Facebook Page (of the pages this token can manage) that has a
    linked Instagram Business Account, per DEC-GRX-023's "no picker UI" scope decision.

    Raises InstagramApiError if the Graph call itself fails; returns None if the call
    succeeds but no page has a linked Instagram Business Account (a distinct, expected
    outcome the caller maps to its own typed error).
    """
    url = f"{_GRAPH_API_BASE}/{api_version}/me/accounts"
    params = {
        "fields": "id,access_token,instagram_business_account{id,username}",
        "access_token": user_access_token,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise InstagramApiError(str(exc)) from exc
    data = _extract_or_raise(response)

    for page in data.get("data", []):
        ig_account = page.get("instagram_business_account")
        if ig_account:
            return ResolvedInstagramAccount(
                facebook_page_id=str(page["id"]),
                ig_business_account_id=str(ig_account["id"]),
                ig_username=ig_account.get("username"),
                page_access_token=str(page["access_token"]),
            )
    raise NoLinkedInstagramAccountError(
        "No connected Facebook Page has a linked Instagram Business Account"
    )


class NoLinkedInstagramAccountError(InstagramApiError):
    """Raised when the Graph API call succeeds but no accessible Page has a linked
    Instagram Business Account — a distinct, expected outcome from a raw API failure."""
