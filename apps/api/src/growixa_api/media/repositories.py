import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.media.models import MediaAsset, MediaFolder


async def create_folder_repo(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    name: str,
    parent_id: uuid.UUID | None = None,
) -> MediaFolder:
    folder = MediaFolder(
        account_id=account_id,
        name=name.strip(),
        parent_id=parent_id,
    )
    session.add(folder)
    await session.flush()
    return folder


async def list_folders_repo(
    session: AsyncSession,
    account_id: uuid.UUID,
) -> Sequence[MediaFolder]:
    query = (
        select(MediaFolder)
        .where(MediaFolder.account_id == account_id)
        .order_by(MediaFolder.name.asc())
    )
    result = await session.execute(query)
    return result.scalars().all()


async def get_folder_by_id_repo(
    session: AsyncSession,
    account_id: uuid.UUID,
    folder_id: uuid.UUID,
) -> MediaFolder | None:
    query = select(MediaFolder).where(
        MediaFolder.account_id == account_id,
        MediaFolder.id == folder_id,
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_media_asset_repo(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    folder_id: uuid.UUID | None,
    filename: str,
    storage_path: str,
    public_url: str,
    media_type: str,
    mime_type: str,
    file_size_bytes: int,
    metadata_info: dict[str, object] | None = None,
    created_by_user_id: uuid.UUID | None = None,
) -> MediaAsset:
    asset = MediaAsset(
        account_id=account_id,
        folder_id=folder_id,
        filename=filename,
        storage_path=storage_path,
        public_url=public_url,
        media_type=media_type,
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        metadata_info=metadata_info or {},
        created_by_user_id=created_by_user_id,
    )
    session.add(asset)
    await session.flush()
    return asset


async def list_media_assets_repo(
    session: AsyncSession,
    account_id: uuid.UUID,
    *,
    folder_id: uuid.UUID | None = None,
    media_type: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[MediaAsset], int, int]:
    query = select(MediaAsset).where(MediaAsset.account_id == account_id)
    if folder_id is not None:
        query = query.where(MediaAsset.folder_id == folder_id)
    if media_type is not None:
        query = query.where(MediaAsset.media_type == media_type.upper())
    if search:
        query = query.where(MediaAsset.filename.ilike(f"%{search.strip()}%"))

    # Total count
    count_query = select(func.count(MediaAsset.id)).where(MediaAsset.account_id == account_id)
    if folder_id is not None:
        count_query = count_query.where(MediaAsset.folder_id == folder_id)
    if media_type is not None:
        count_query = count_query.where(MediaAsset.media_type == media_type.upper())
    if search:
        count_query = count_query.where(MediaAsset.filename.ilike(f"%{search.strip()}%"))

    # Total bytes
    bytes_query = select(func.coalesce(func.sum(MediaAsset.file_size_bytes), 0)).where(
        MediaAsset.account_id == account_id
    )

    total_count = (await session.execute(count_query)).scalar_one() or 0
    total_bytes = (await session.execute(bytes_query)).scalar_one() or 0

    query = query.order_by(MediaAsset.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return result.scalars().all(), total_count, total_bytes


async def get_media_asset_repo(
    session: AsyncSession,
    account_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> MediaAsset | None:
    query = select(MediaAsset).where(
        MediaAsset.account_id == account_id,
        MediaAsset.id == asset_id,
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def delete_media_asset_repo(
    session: AsyncSession,
    account_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> bool:
    query = delete(MediaAsset).where(
        MediaAsset.account_id == account_id,
        MediaAsset.id == asset_id,
    )
    result = await session.execute(query)
    return result.rowcount > 0  # type: ignore[attr-defined]
