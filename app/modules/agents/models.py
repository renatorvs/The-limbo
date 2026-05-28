from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime


class AgentAction(Base):
    """HI-C: actions proposed by agents that require human approval."""

    __tablename__ = "agent_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    agent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)  # e.g. create_campaign, move_roadmap
    description = Column(Text, nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class AgentOrchestrationRun(Base):
    """Audit log for multi-agent orchestration runs."""

    __tablename__ = "agent_orchestration_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    objective = Column(Text, nullable=False)
    agents_used = Column(JSON, default=list)
    steps = Column(JSON, default=list)
    synthesis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
