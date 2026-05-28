from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID


class MvpGoalUpdate(BaseModel):
    domain: str
    metric_key: str
    target_value: float
    deadline: Optional[date] = None
    notes: Optional[str] = None


class MvpKpiItem(BaseModel):
    key: str
    label: str
    unit: str
    current_value: Optional[float] = None
    target_value: float
    status: str  # on_track, at_risk, off_track, no_data
    direction: str
    gap_percent: Optional[float] = None


class MvpDomainDashboard(BaseModel):
    domain: str
    label: str
    kpis: List[MvpKpiItem]
    on_track_count: int
    at_risk_count: int


class MvpDashboard(BaseModel):
    company_id: str
    company_name: Optional[str] = None
    domains: List[MvpDomainDashboard]
    overall_health: str  # green, yellow, red


class PromptFavoriteCreate(BaseModel):
    agent_id: str
    label: str
    prompt_text: str


class PromptFavoriteOut(BaseModel):
    id: UUID
    agent_id: str
    label: str
    prompt_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class PromptHistoryOut(BaseModel):
    id: UUID
    agent_id: str
    prompt_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class PromptSuggestionOut(BaseModel):
    label: str
    prompt: str
