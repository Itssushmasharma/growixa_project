import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class Condition(BaseModel):
    field: str
    operator: str
    value: Any

class Action(BaseModel):
    type: str
    config: Dict[str, Any]

class WorkflowIn(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    conditions: List[Condition] = []
    actions: List[Action] = []

class WorkflowOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    trigger_type: str
    conditions: List[Condition] = []
    actions: List[Action] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
