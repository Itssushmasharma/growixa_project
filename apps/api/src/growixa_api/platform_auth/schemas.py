import uuid

from pydantic import BaseModel


class PlatformLoginIn(BaseModel):
    email: str
    password: str


class PlatformLoginOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    role: str


class PlatformMeOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    permissions: list[str]
