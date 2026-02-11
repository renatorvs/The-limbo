from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

# Pelo schema, parece que inputs de sessão/mensagem são complexos.
# Vamos focar no ChatRequest que o frontend já usa.

class ChatRequest(BaseModel):
    user_message: str
    session_id: Optional[str] = None
    company_id: Optional[str] = None # Para contexto multi-tenant

class AdvisoryResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str] = []

class KnowledgeBaseItemCreate(BaseModel):
    content: str
    source_title: str
    source_type: str
    company_id: Optional[UUID]

class KnowledgeBaseItemOut(BaseModel):
    id: UUID
    source_title: str
    created_at: datetime
    
    class Config:
        orm_mode = True
