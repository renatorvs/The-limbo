from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from uuid import UUID

# Customer
class CustomerBase(BaseModel):
    name: str
    plan_name: str
    mrr_value: float
    health_score: int
    onboarding_status: str
    churned_at: Optional[date]
    external_source_id: Optional[str]
    last_xp_score: Optional[int]

class CustomerCreate(CustomerBase):
    company_id: Optional[UUID]

class CustomerOut(CustomerBase):
    id: UUID
    company_id: UUID

    class Config:
        orm_mode = True

# Ticket
class TicketBase(BaseModel):
    title: str
    category: str
    severity: str
    status: str
    external_ticket_id: Optional[str]

class TicketCreate(TicketBase):
    customer_id: UUID

class TicketOut(TicketBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# NPS Survey
class NpsSurveyBase(BaseModel):
    score: int
    comment: Optional[str]

class NpsSurveyCreate(NpsSurveyBase):
    user_id: UUID
    company_id: UUID

class NpsSurveyOut(NpsSurveyBase):
    id: UUID
    responded_at: datetime
    
    class Config:
        orm_mode = True

# Dashboard Stats
class DashboardStats(BaseModel):
    churn_rate: float
    nps_score: int
    expansion_revenue: float
    total_mrr: float
    active_customers: int
    nps_promoters_pct: int
    nps_neutrals_pct: int
    nps_detractors_pct: int

