import httpx

_TIMEOUT_SECONDS = 20.0


class StorageError(Exception):
    """Wraps any failure talking to Supabase Storage's REST API (network, or a
    non-2xx/error response) behind one type, mirroring smtp_transport.py's
    EmailSendError shape."""


async def upload_object(
    *,
    storage_url: str,
    service_key: str,
    bucket: str,
    path: str,
    content: bytes,
    content_type: str,
) -> str:
    """Uploads `content` to `{bucket}/{path}` and returns its public URL.

    Per DEC-GRX-024, this bucket is public-read by requirement (Instagram's Content
    Publishing API fetches media by plain URL, with no auth header support) — the
    returned URL is immediately usable as-is, no signing step.
    """
    url = f"{storage_url}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "apikey": service_key,
        "Content-Type": content_type,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=headers, content=content)
    except httpx.HTTPError as exc:
        raise StorageError(str(exc)) from exc
    if response.is_error:
        raise StorageError(
            f"Supabase Storage upload failed (HTTP {response.status_code}): {response.text}"
        )
    return f"{storage_url}/storage/v1/object/public/{bucket}/{path}"


async def delete_object(*, storage_url: str, service_key: str, bucket: str, path: str) -> None:
    url = f"{storage_url}/storage/v1/object/{bucket}/{path}"
    headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.delete(url, headers=headers)
    except httpx.HTTPError as exc:
        raise StorageError(str(exc)) from exc
    if response.is_error:
        raise StorageError(
            f"Supabase Storage delete failed (HTTP {response.status_code}): {response.text}"
        )
