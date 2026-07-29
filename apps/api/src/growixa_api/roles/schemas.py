import uuid

from pydantic import BaseModel


class RoleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
