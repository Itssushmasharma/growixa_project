import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.db import get_session
from growixa_api.media.schemas import (
    MediaAssetOut,
    MediaFolderCreateIn,
    MediaFolderOut,
    MediaListResponse,
)
from growixa_api.media.services import (
    MediaAssetNotFoundError,
    MediaValidationError,
    create_folder_service,
    delete_asset_service,
    list_folders_service,
    list_media_service,
    upload_asset_service,
)
from growixa_api.permissions.dependencies import get_current_account_id, require_permission

router = APIRouter(prefix="/media", tags=["media"])

_require_social_view = require_permission("social.view")
_require_social_manage = require_permission("social.manage")


@router.get("", response_model=MediaListResponse)
async def list_media_route(
    folder_id: uuid.UUID | None = Query(None),
    media_type: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _actor_id: uuid.UUID = Depends(_require_social_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> MediaListResponse:
    assets, folders, total_assets, total_bytes = await list_media_service(
        session,
        account_id,
        folder_id=folder_id,
        media_type=media_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    return MediaListResponse(
        assets=[MediaAssetOut.model_validate(a) for a in assets],
        folders=[MediaFolderOut.model_validate(f) for f in folders],
        total_assets=total_assets,
        total_bytes=total_bytes,
    )


@router.post("/upload", response_model=MediaAssetOut, status_code=status.HTTP_201_CREATED)
async def upload_asset_route(
    file: UploadFile = File(...),
    folder_id: uuid.UUID | None = Form(None),
    actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> MediaAssetOut:
    content = await file.read()
    try:
        asset = await upload_asset_service(
            session,
            account_id=account_id,
            folder_id=folder_id,
            filename=file.filename or "media_file",
            content=content,
            content_type=file.content_type or "application/octet-stream",
            actor_id=actor_id,
        )
    except MediaValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return MediaAssetOut.model_validate(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_route(
    asset_id: uuid.UUID,
    _actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await delete_asset_service(session, account_id, asset_id)
    except MediaAssetNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/folders", response_model=list[MediaFolderOut])
async def list_folders_route(
    _actor_id: uuid.UUID = Depends(_require_social_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> list[MediaFolderOut]:
    folders = await list_folders_service(session, account_id)
    return [MediaFolderOut.model_validate(f) for f in folders]


@router.post("/folders", response_model=MediaFolderOut, status_code=status.HTTP_201_CREATED)
async def create_folder_route(
    payload: MediaFolderCreateIn,
    _actor_id: uuid.UUID = Depends(_require_social_manage),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> MediaFolderOut:
    folder = await create_folder_service(
        session,
        account_id=account_id,
        name=payload.name,
        parent_id=payload.parent_id,
    )
    return MediaFolderOut.model_validate(folder)
