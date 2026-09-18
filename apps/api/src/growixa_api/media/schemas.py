import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class MediaFolderCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: uuid.UUID | None = None


class MediaFolderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class MediaAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    folder_id: uuid.UUID | None
    filename: str
    storage_path: str
    public_url: str
    media_type: str
    mime_type: str
    file_size_bytes: int
    metadata_info: dict[str, object] = Field(default_factory=dict, exclude=True)
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def metadata(self) -> dict[str, object]:
        return self.metadata_info

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_name(self) -> str:
        return self.filename


class MediaListResponse(BaseModel):
    assets: list[MediaAssetOut]
    folders: list[MediaFolderOut]
    total_assets: int
    total_bytes: int
