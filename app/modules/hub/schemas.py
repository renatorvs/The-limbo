from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.modules.reports.schemas import AppReportIngest


class HubInputResponse(BaseModel):
    app_key: str
    report_id: UUID
    output_id: UUID
    message: str


class KpiAlert(BaseModel):
    domain: str
    metric: str
    label: str
    current: Optional[float]
    target: float
    status: str
    gap_percent: Optional[float] = None


class HubOutput(BaseModel):
    app_key: str
    product_name: str
    generated_at: datetime
    briefing: str
    kpi_alerts: List[KpiAlert] = []
    recommendations: List[str] = []
    approved_actions: List[Dict[str, Any]] = []
    pending_approval: List[Dict[str, Any]] = []
    goal_adjustments: List[Dict[str, Any]] = []
    metrics_snapshot: Dict[str, float] = {}
    output_id: UUID


class ProductStatus(BaseModel):
    app_key: str
    name: str
    company_id: Optional[str] = None
    last_input_at: Optional[datetime] = None
    last_output_at: Optional[datetime] = None
    overall_health: Optional[str] = None
    has_pending_output: bool = False
