from pydantic import BaseModel
from datetime import date
from typing import Optional
from uuid import UUID

# Campaign
class CampaignBase(BaseModel):
    name: str
    channel: str
    status: str
    budget_total: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class CampaignCreate(CampaignBase):
    company_id: Optional[UUID] = None

class CampaignOut(CampaignBase):
    id: UUID
    company_id: UUID

    class Config:
        orm_mode = True

# Funnel Snapshot
class FunnelSnapshotBase(BaseModel):
    date: date
    visitors: int
    leads: int
    mql: int
    sql: int
    customers: int
    cac: float

class FunnelSnapshotCreate(FunnelSnapshotBase):
    company_id: Optional[UUID] = None

class FunnelSnapshotOut(FunnelSnapshotBase):
    id: UUID
    company_id: UUID

    class Config:
        orm_mode = True

class GrowthDashboardStats(BaseModel):
    arr: float
    ltv: float
    churn_rate: float
    cac: float
    quick_ratio: float
    nps: int
    star_metric: int # North Star Metric

