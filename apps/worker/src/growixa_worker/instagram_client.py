from typing import Any

import httpx

_GRAPH_API_BASE = "https://graph.facebook.com"
_TIMEOUT_SECONDS = 20.0
# Graph API error code 190 = invalid/expired OAuth access token -- a dead token can
# never succeed on retry, so it's classified separately from a transient failure.
_DEAD_TOKEN_ERROR_CODE = 190


class InstagramPublishError(Exception):
    """Base class for any failure publishing to Instagram."""


class PermanentPublishError(InstagramPublishError):
    """The token is dead (Graph error code 190) or the request is otherwise
    structurally invalid -- retrying will never succeed. Short-circuits the worker's
    retry ladder; surfaces as "reconnect required" (THREAT_MODEL.md T49)."""


class TransientPublishError(InstagramPublishError):
    """Rate limits, timeouts, or a container stuck in ERROR/EXPIRED -- may succeed on a
    later attempt, so it's routed through the normal retry/DLQ ladder."""


def _classify_and_raise(data: dict[str, Any], *, status_code: int) -> None:
    error = data.get("error")
    if error is not None:
        if error.get("code") == _DEAD_TOKEN_ERROR_CODE:
            raise PermanentPublishError(
                f"{error.get('type', 'GraphError')}: {error.get('message')}"
            )
        raise TransientPublishError(f"{error.get('type', 'GraphError')}: {error.get('message')}")
    raise TransientPublishError(f"Graph API returned HTTP {status_code}: {data}")


async def _get(url: str, params: dict[str, str]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise TransientPublishError(str(exc)) from exc
    data: dict[str, Any] = response.json()
    if response.is_error or "error" in data:
        _classify_and_raise(data, status_code=response.status_code)
    return data


async def _post(url: str, params: dict[str, str]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, params=params)
    except httpx.HTTPError as exc:
        raise TransientPublishError(str(exc)) from exc
    data: dict[str, Any] = response.json()
    if response.is_error or "error" in data:
        _classify_and_raise(data, status_code=response.status_code)
    return data


async def create_media_container(
    *,
    ig_business_account_id: str,
    page_access_token: str,
    image_url: str,
    caption: str,
    api_version: str,
) -> str:
    url = f"{_GRAPH_API_BASE}/{api_version}/{ig_business_account_id}/media"
    data = await _post(
        url, {"image_url": image_url, "caption": caption, "access_token": page_access_token}
    )
    return str(data["id"])


async def poll_container_status(
    *, container_id: str, page_access_token: str, api_version: str
) -> str:
    """Returns the container's `status_code`: IN_PROGRESS, FINISHED, ERROR, or EXPIRED."""
    url = f"{_GRAPH_API_BASE}/{api_version}/{container_id}"
    data = await _get(url, {"fields": "status_code", "access_token": page_access_token})
    return str(data["status_code"])


async def publish_container(
    *, ig_business_account_id: str, container_id: str, page_access_token: str, api_version: str
) -> str:
    url = f"{_GRAPH_API_BASE}/{api_version}/{ig_business_account_id}/media_publish"
    data = await _post(url, {"creation_id": container_id, "access_token": page_access_token})
    return str(data["id"])


async def fetch_permalink(*, media_id: str, page_access_token: str, api_version: str) -> str | None:
    """Best-effort -- a missing permalink doesn't mean the publish failed, so this
    never raises; the caller stores whatever it gets (including None)."""
    url = f"{_GRAPH_API_BASE}/{api_version}/{media_id}"
    try:
        data = await _get(url, {"fields": "permalink", "access_token": page_access_token})
    except InstagramPublishError:
        return None
    permalink = data.get("permalink")
    return str(permalink) if permalink is not None else None


async def refresh_long_lived_token(
    *, app_id: str, app_secret: str, current_token: str, api_version: str
) -> tuple[str, int]:
    """Re-exchanges a still-valid long-lived token for a fresh one with a renewed ~60
    day expiry -- the same `fb_exchange_token` grant growixa_api's
    exchange_for_long_lived_token uses for the initial exchange. Returns
    (access_token, expires_in_seconds)."""
    url = f"{_GRAPH_API_BASE}/{api_version}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": current_token,
    }
    data = await _get(url, params)
    return str(data["access_token"]), int(data.get("expires_in", 5184000))
