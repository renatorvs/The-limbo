from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime

class Customer(Base):
    __tablename__ = "cs_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    name = Column(String)
    plan_name = Column(String)
    mrr_value = Column(Numeric)
    health_score = Column(Integer)
    onboarding_status = Column(String)
    churned_at = Column(Date)
    external_source_id = Column(String)
    last_xp_score = Column(Integer)
    last_simulados_count = Column(Integer)

class NpsSurvey(Base):
    __tablename__ = "cs_nps_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    score = Column(Integer)
    comment = Column(Text)
    responded_at = Column(DateTime, default=datetime.utcnow)

class Ticket(Base):
    __tablename__ = "cs_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("cs_customers.id"))
    title = Column(String)
    category = Column(String)
    severity = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    external_ticket_id = Column(String)
