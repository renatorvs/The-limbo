from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class ChatRequest(BaseModel):
    user_message: str
    session_id: Optional[str] = None
    company_id: Optional[str] = None
    agent_id: Optional[str] = "cfo"


class AdvisoryResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str] = []
    agent_id: Optional[str] = None
    tools_used: List[str] = []


class AgentStepResult(BaseModel):
    agent_id: str
    label: str
    response: str
    tools_used: List[str] = []


class OrchestrationRequest(BaseModel):
    objective: str
    company_id: Optional[str] = None
    company_ids: Optional[List[str]] = None
    agents: Optional[List[str]] = None


class OrchestrationResponse(BaseModel):
    objective: str
    company_id: Optional[str] = None
    steps: List[AgentStepResult] = []
    synthesis: str
    pending_actions: List[Dict[str, Any]] = []


class CompanyOrchestrationResult(BaseModel):
    company_id: str
    company_name: Optional[str] = None
    steps: List[AgentStepResult] = []
    synthesis: str
    pending_actions: List[Dict[str, Any]] = []


class MultiOrchestrationResponse(BaseModel):
    objective: str
    companies: List[CompanyOrchestrationResult] = []
    portfolio_synthesis: str


class KnowledgeBaseItemCreate(BaseModel):
    content: str
    source_title: str
    source_type: str
    company_id: Optional[UUID] = None


class KnowledgeBaseItemOut(BaseModel):
    id: UUID
    source_title: str
    created_at: datetime

    class Config:
        from_attributes = True
