from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime

class Campaign(Base):
    __tablename__ = "growth_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    name = Column(String)
    channel = Column(String)
    status = Column(String)
    budget_total = Column(Numeric)
    start_date = Column(Date)
    end_date = Column(Date)

class FunnelSnapshot(Base):
    __tablename__ = "growth_funnel_snapshot"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    date = Column(Date)
    visitors = Column(Integer)
    leads = Column(Integer)
    mql = Column(Integer)
    sql = Column(Integer)
    customers = Column(Integer)
    cac = Column(Numeric)
