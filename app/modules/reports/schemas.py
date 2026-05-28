from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from uuid import UUID


class CompanyRef(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    key: Optional[str] = None


class ReportPeriod(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None


class DomainReport(BaseModel):
    metrics: Dict[str, float] = {}
    highlights: List[str] = []
    risks: List[str] = []
    recommendations: List[str] = []


class ProposedAction(BaseModel):
    agent_id: str = "ceo"
    action_type: str
    description: str
    payload: Dict[str, Any] = {}


class AppReportIngest(BaseModel):
    limbo_report_version: str = "1.0"
    company_ref: CompanyRef
    source_app: str
    generated_at: Optional[datetime] = None
    generated_by_agent: Optional[str] = None
    period: Optional[ReportPeriod] = None
    executive_summary: Optional[str] = None
    domains: Dict[str, DomainReport] = {}
    actions_proposed: List[ProposedAction] = []


class ReportIngestResponse(BaseModel):
    report_id: UUID
    company_id: str
    metrics_extracted: int
    knowledge_indexed: bool
    actions_queued: int
    message: str


class ReportSummaryOut(BaseModel):
    id: UUID
    source_app: str
    generated_by_agent: Optional[str]
    period_end: Optional[date]
    executive_summary: Optional[str]
    ingested_at: datetime
    metrics_count: int

    class Config:
        from_attributes = True
