from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime


class CompanyReport(Base):
    """Relatório enviado por agentes de apps externas — fonte primária de dados."""

    __tablename__ = "company_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    source_app = Column(String, nullable=False)       # ex: sofia, startup-b
    generated_by_agent = Column(String, nullable=True)
    report_version = Column(String, default="1.0")
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    executive_summary = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=False)
    parsed_metrics = Column(JSON, default=dict)     # flat metric_key → value
    domain_narratives = Column(JSON, default=dict)  # per domain highlights/risks
    generated_at = Column(DateTime, nullable=True)    # timestamp from report
    ingested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")       # active, superseded, error
