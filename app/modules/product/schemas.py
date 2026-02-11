from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from uuid import UUID

# Roadmap
class RoadmapItemBase(BaseModel):
    title: str
    description: Optional[str]
    status: str
    priority: str
    strategic_goal: Optional[str]
    target_date: Optional[date]

class RoadmapItemCreate(RoadmapItemBase):
    company_id: Optional[UUID] = None

class RoadmapItemOut(RoadmapItemBase):
    id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Engineering Metrics
class EngineeringMetricsBase(BaseModel):
    metric_name: str
    value: float
    measured_at: date

class EngineeringMetricsCreate(EngineeringMetricsBase):
    company_id: Optional[UUID] = None

class EngineeringMetricsOut(EngineeringMetricsBase):
    id: UUID
    company_id: Optional[UUID] = None

    class Config:
        orm_mode = True
