from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    cnpj_or_tax_id = Column(String)
    industry = Column(String)
    logo_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="company")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="users")

class CompanyLiveStats(Base):
    __tablename__ = "company_live_stats"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), primary_key=True)
    current_mrr = Column(Numeric)
    current_arr = Column(Numeric)
    total_active_customers = Column(Integer)
    total_trials_active = Column(Integer)
    last_updated_at = Column(DateTime, default=datetime.utcnow)

class AnalyticsSaasMetricsDaily(Base):
    __tablename__ = "analytics_saas_metrics_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    reference_date = Column(Date)
    
    mrr = Column(Numeric)
    arr = Column(Numeric)
    arpu = Column(Numeric)
    expansion_mrr = Column(Numeric)
    churn_rate_percent = Column(Numeric)
    nrr_percent = Column(Numeric)
    ltv = Column(Numeric)
    nps_score = Column(Integer)
    cac = Column(Numeric)
    ltv_cac_ratio = Column(Numeric)
    payback_period_months = Column(Numeric)
    trial_conversion_rate = Column(Numeric)
    dau = Column(Integer)
    mau = Column(Integer)
    activation_rate_percent = Column(Numeric)
    
    created_at = Column(DateTime, default=datetime.utcnow)
