import mimetypes
import uuid
from collections.abc import Sequence
from contextlib import suppress

from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.config import get_settings
from growixa_api.files import storage_client
from growixa_api.files.storage_client import StorageError
from growixa_api.media import repositories
from growixa_api.media.models import MediaAsset, MediaFolder

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
_ALLOWED_DOC_TYPES = {"application/pdf"}

_MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15MB
_MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100MB
_MAX_DOC_BYTES = 25 * 1024 * 1024  # 25MB


class MediaValidationError(Exception):
    pass


class MediaAssetNotFoundError(Exception):
    pass


def _detect_media_type(mime_type: str) -> str:
    if mime_type in _ALLOWED_IMAGE_TYPES:
        return "IMAGE"
    if mime_type in _ALLOWED_VIDEO_TYPES:
        return "VIDEO"
    if mime_type in _ALLOWED_DOC_TYPES:
        return "DOCUMENT"
    raise MediaValidationError(
        f"Unsupported file type: {mime_type}. Supported: JPEG, PNG, WebP, GIF, MP4, WebM, PDF."
    )


def _validate_file_size(media_type: str, file_size: int) -> None:
    if media_type == "IMAGE" and file_size > _MAX_IMAGE_BYTES:
        raise MediaValidationError(
            f"Image exceeds maximum size of {_MAX_IMAGE_BYTES // (1024 * 1024)}MB"
        )
    if media_type == "VIDEO" and file_size > _MAX_VIDEO_BYTES:
        raise MediaValidationError(
            f"Video exceeds maximum size of {_MAX_VIDEO_BYTES // (1024 * 1024)}MB"
        )
    if media_type == "DOCUMENT" and file_size > _MAX_DOC_BYTES:
        raise MediaValidationError(
            f"Document exceeds maximum size of {_MAX_DOC_BYTES // (1024 * 1024)}MB"
        )


async def upload_asset_service(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    folder_id: uuid.UUID | None,
    filename: str,
    content: bytes,
    content_type: str,
    actor_id: uuid.UUID | None = None,
) -> MediaAsset:
    clean_mime = (content_type or "").lower().split(";")[0].strip()
    if not clean_mime or clean_mime == "application/octet-stream":
        guessed, _ = mimetypes.guess_type(filename)
        clean_mime = guessed or "application/octet-stream"

    media_type = _detect_media_type(clean_mime)
    _validate_file_size(media_type, len(content))

    asset_id = uuid.uuid4()
    ext = mimetypes.guess_extension(clean_mime) or ".bin"
    if ext == ".jpe":
        ext = ".jpg"

    storage_path = f"media/{account_id}/{asset_id}{ext}"
    settings = get_settings()

    if settings.supabase_storage_url and settings.supabase_storage_service_key:
        try:
            public_url = await storage_client.upload_object(
                storage_url=settings.supabase_storage_url,
                service_key=settings.supabase_storage_service_key,
                bucket=settings.supabase_storage_bucket,
                path=storage_path,
                content=content,
                content_type=clean_mime,
            )
        except StorageError as exc:
            raise MediaValidationError(f"Storage upload failed: {exc}") from exc
    else:
        # Development / test storage mock URL
        public_url = f"https://mock-storage.growixa.local/{storage_path}"

    asset = await repositories.create_media_asset_repo(
        session,
        account_id=account_id,
        folder_id=folder_id,
        filename=filename,
        storage_path=storage_path,
        public_url=public_url,
        media_type=media_type,
        mime_type=clean_mime,
        file_size_bytes=len(content),
        metadata_info={"original_filename": filename, "extension": ext},
        created_by_user_id=actor_id,
    )
    await session.commit()
    return asset


async def list_media_service(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    folder_id: uuid.UUID | None = None,
    media_type: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[MediaAsset], Sequence[MediaFolder], int, int]:
    assets, total_assets, total_bytes = await repositories.list_media_assets_repo(
        session,
        account_id,
        folder_id=folder_id,
        media_type=media_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    folders = await repositories.list_folders_repo(session, account_id)
    return assets, folders, total_assets, total_bytes


async def delete_asset_service(
    session: AsyncSession,
    account_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    asset = await repositories.get_media_asset_repo(session, account_id, asset_id)
    if asset is None:
        raise MediaAssetNotFoundError("Media asset not found")

    settings = get_settings()
    if settings.supabase_storage_url and settings.supabase_storage_service_key:
        with suppress(StorageError):
            await storage_client.delete_object(
                storage_url=settings.supabase_storage_url,
                service_key=settings.supabase_storage_service_key,
                bucket=settings.supabase_storage_bucket,
                path=asset.storage_path,
            )

    await repositories.delete_media_asset_repo(session, account_id, asset_id)
    await session.commit()


async def create_folder_service(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    name: str,
    parent_id: uuid.UUID | None = None,
) -> MediaFolder:
    folder = await repositories.create_folder_repo(
        session,
        account_id=account_id,
        name=name,
        parent_id=parent_id,
    )
    await session.commit()
    return folder


async def list_folders_service(
    session: AsyncSession,
    account_id: uuid.UUID,
) -> Sequence[MediaFolder]:
    return await repositories.list_folders_repo(session, account_id)
