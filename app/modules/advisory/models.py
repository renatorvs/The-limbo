from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.core.database import Base
import uuid
from datetime import datetime

class AdvisoryKnowledgeBase(Base):
    __tablename__ = "advisory_knowledge_base"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    content = Column(Text, nullable=False)
    source_type = Column(String)
    source_title = Column(String)
    metadata_ = Column("metadata", JSON) # Use JSON for compatibility
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdvisorySession(Base):
    __tablename__ = "advisory_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdvisoryMessage(Base):
    __tablename__ = "advisory_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("advisory_sessions.id"))
    role = Column(String) # user, assistant
    content = Column(Text)
    referenced_sources = Column(JSON) # Use JSON for compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
