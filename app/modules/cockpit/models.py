from sqlalchemy import Column, String, Text, DateTime, Numeric, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid
from datetime import datetime


class MvpGoal(Base):
    """Metas editáveis por startup e KPI."""

    __tablename__ = "mvp_goals"
    __table_args__ = (
        UniqueConstraint("company_id", "domain", "metric_key", name="uq_mvp_goal"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    domain = Column(String, nullable=False)  # cfo, cmo, cpo, cs
    metric_key = Column(String, nullable=False)
    target_value = Column(Numeric, nullable=False)
    deadline = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptHistory(Base):
    """Histórico de prompts usados, por área."""

    __tablename__ = "prompt_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    agent_id = Column(String, nullable=False)
    prompt_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PromptFavorite(Base):
    """Prompts favoritos do usuário, por área."""

    __tablename__ = "prompt_favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    agent_id = Column(String, nullable=False)
    label = Column(String, nullable=False)
    prompt_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
