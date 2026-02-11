from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.core.models import User
from . import schemas, agent, models
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def view_dashboard(
    request: Request, 
    session_id: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    # 1. Fetch recent sessions for CURRENT USER
    sessions = db.query(models.AdvisorySession).filter(
        models.AdvisorySession.user_id == current_user.id
    ).order_by(models.AdvisorySession.created_at.desc()).limit(10).all()

    active_session = None
    messages = []
    
    if session_id:
        try:
             # Verify session belongs to user
             print(f"DEBUG: Looking for session {session_id} for user {current_user.id}")
             active_session = db.query(models.AdvisorySession).filter(
                 models.AdvisorySession.id == session_id,
                 models.AdvisorySession.user_id == current_user.id
             ).first()
             print(f"DEBUG: Found session: {active_session}")
             
             if active_session:
                 messages = db.query(models.AdvisoryMessage).filter(models.AdvisoryMessage.session_id == session_id).order_by(models.AdvisoryMessage.created_at.asc()).all()
        except Exception as e:
            print(f"Error fetching session: {e}")
            
    # 2. Fetch Knowledge Base Items (Filtered by Company)
    knowledge_base = db.query(models.AdvisoryKnowledgeBase).filter(
        models.AdvisoryKnowledgeBase.company_id == current_user.company_id
    ).order_by(models.AdvisoryKnowledgeBase.created_at.desc()).limit(5).all()

    return templates.TemplateResponse("dashboard/advisory.html", {
        "request": request,
        "sessions": sessions,
        "active_session": active_session,
        "messages": messages,
        "knowledge_base": knowledge_base,
        "current_session_id": session_id
    })
    
@router.post("/dashboard/new")
def create_new_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    # Create a new session
    new_session = models.AdvisorySession(
        title="Nova Sessão de Consultoria",
        user_id=current_user.id, 
        company_id=current_user.company_id 
    )
    db.add(new_session)
    db.commit()
    return RedirectResponse(url=f"/api/v1/advisory/dashboard?session_id={new_session.id}", status_code=303)

@router.post("/dashboard/chat", response_class=RedirectResponse)
async def chat_interaction(
    request: Request,
    session_id: str = Form(...),
    user_message: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    # Verify session access
    session = db.query(models.AdvisorySession).filter(
        models.AdvisorySession.id == session_id,
        models.AdvisorySession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    # 1. Save User Message
    user_msg_db = models.AdvisoryMessage(
        session_id=session_id,
        role="user",
        content=user_message
    )
    db.add(user_msg_db)
    db.commit()
    
    # 2. Call Agent
    try:
        chat_req = schemas.ChatRequest(
            user_message=user_message,
            session_id=session_id,
            company_id=str(current_user.company_id) if current_user.company_id else None
        )
        
        # Pass user context
        user_context = {
            "user_id": str(current_user.id),
            "company_id": str(current_user.company_id) if current_user.company_id else None
        }
        
        agent_resp = await agent.run_agent(chat_req, user_context)
        
        # We need to ensure the agent response is saved in the DB.
        # Let's check if the standard agent flow saves it. 
        # If not, we save it here.
        
        assistant_msg_db = models.AdvisoryMessage(
            session_id=session_id,
            role="assistant",
            content=agent_resp.response,
            referenced_sources=agent_resp.sources # Assuming sources is a list of strings
        )
        db.add(assistant_msg_db)
        db.commit()
        
    except Exception as e:
        print(f"Error calling agent: {e}")
        # Fallback error message
        db.add(models.AdvisoryMessage(
            session_id=session_id,
            role="assistant", 
            content="Desculpe, ocorreu um erro ao processar sua solicitação."
        ))
        db.commit()

    return RedirectResponse(url=f"/api/v1/advisory/dashboard?session_id={session_id}", status_code=303)

@router.post("/chat/ask", response_model=schemas.AdvisoryResponse)
async def ask_advisor(request: schemas.ChatRequest):
    return await agent.run_agent(request)

@router.get("/knowledge", response_model=list[schemas.KnowledgeBaseItemOut])
def get_knowledge_base(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.AdvisoryKnowledgeBase).offset(skip).limit(limit).all()

@router.post("/knowledge", response_model=schemas.KnowledgeBaseItemOut)
def add_knowledge_item(item: schemas.KnowledgeBaseItemCreate, db: Session = Depends(get_db)):
    # Note: Embedding generation would typically happen here or in a background task
    db_item = models.AdvisoryKnowledgeBase(
        content=item.content,
        source_title=item.source_title,
        source_type=item.source_type,
        company_id=item.company_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
