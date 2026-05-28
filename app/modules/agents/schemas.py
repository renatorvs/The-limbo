from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class AgentActionOut(BaseModel):
    id: UUID
    agent_id: str
    action_type: str
    description: str
    payload: Dict[str, Any] = {}
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AgentActionResolve(BaseModel):
    status: str  # approved or rejected
