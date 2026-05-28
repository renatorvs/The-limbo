from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime


class LimboOutput(Base):
    """OUTPUT gerado pelo Limbo para apps consumirem (Sofia, BodyVision)."""

    __tablename__ = "limbo_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    app_key = Column(String, nullable=False, index=True)
    source_report_id = Column(UUID(as_uuid=True), ForeignKey("company_reports.id"), nullable=True)
    briefing = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    consumed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
