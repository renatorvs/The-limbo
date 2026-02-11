from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime

class RoadmapItem(Base):
    __tablename__ = "product_roadmap"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    strategic_goal = Column(Text)
    target_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

class EngineeringMetrics(Base):
    __tablename__ = "product_engineering_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    metric_name = Column(String)
    value = Column(Numeric)
    measured_at = Column(Date)

class DailyActiveUsers(Base):
    __tablename__ = "product_daily_active_users"

    # Composite primary key implicitly via unique constraints often, but here using date+id as logic
    # Actually schema has no ID, just date and company_id. SQLAlchemy desires a PK.
    # We will use composite PK.
    date = Column(Date, primary_key=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), primary_key=True)
    dau_count = Column(Integer)
    mau_count = Column(Integer)

class UserActivity(Base):
    __tablename__ = "product_user_activity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_name = Column(String)
    feature_group = Column(String)
    performed_at = Column(DateTime, default=datetime.utcnow)
