from typing import Optional, List

from fastapi import APIRouter, Request, Depends, HTTPException, Form

from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core import security

from app.core.models import User

from . import schemas, agent, models

from app.modules.cockpit import service as cockpit_service, prompt_library

import uuid



router = APIRouter()

templates = Jinja2Templates(directory="app/templates")



@router.get("/dashboard")

def view_dashboard(

    request: Request,

    session_id: Optional[str] = None,

    agent: Optional[str] = "cfo",

    prompt: Optional[str] = None,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user)

):

    sessions = db.query(models.AdvisorySession).filter(

        models.AdvisorySession.user_id == current_user.id

    ).order_by(models.AdvisorySession.created_at.desc()).limit(10).all()



    active_session = None

    messages = []



    if session_id:

        try:

            active_session = db.query(models.AdvisorySession).filter(

                models.AdvisorySession.id == session_id,

                models.AdvisorySession.user_id == current_user.id

            ).first()

            if active_session:

                messages = db.query(models.AdvisoryMessage).filter(

                    models.AdvisoryMessage.session_id == session_id

                ).order_by(models.AdvisoryMessage.created_at.asc()).all()

        except Exception as e:

            print(f"Error fetching session: {e}")



    knowledge_base = db.query(models.AdvisoryKnowledgeBase).filter(

        models.AdvisoryKnowledgeBase.company_id == current_user.company_id

    ).order_by(models.AdvisoryKnowledgeBase.created_at.desc()).limit(5).all()



    selected_agent = agent or "cfo"

    suggestions = prompt_library.get_suggestions(selected_agent)

    history = cockpit_service.get_history(db, current_user.id, selected_agent, limit=15)

    favorites = cockpit_service.get_favorites(db, current_user.id, selected_agent)

    all_suggestions = prompt_library.get_all_by_domain()



    return templates.TemplateResponse("dashboard/advisory.html", {

        "request": request,

        "sessions": sessions,

        "active_session": active_session,

        "messages": messages,

        "knowledge_base": knowledge_base,

        "current_session_id": session_id,

        "selected_agent": selected_agent,

        "prefill_prompt": prompt or "",

        "suggestions": suggestions,

        "prompt_history": history,

        "prompt_favorites": favorites,

        "all_suggestions": all_suggestions,

        "persona_labels": __import__(

            "app.modules.advisory.prompts", fromlist=["PERSONA_LABELS"]

        ).PERSONA_LABELS,

    })



@router.post("/dashboard/new")

def create_new_chat(

    agent: Optional[str] = Form("cfo"),

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user)

):

    new_session = models.AdvisorySession(

        title="Nova Sessão de Consultoria",

        user_id=current_user.id,

        company_id=current_user.company_id

    )

    db.add(new_session)

    db.commit()

    return RedirectResponse(

        url=f"/api/v1/advisory/dashboard?session_id={new_session.id}&agent={agent}",

        status_code=303,

    )



@router.post("/dashboard/chat", response_class=RedirectResponse)

async def chat_interaction(

    request: Request,

    session_id: str = Form(...),

    user_message: str = Form(...),

    agent_id: str = Form("cfo"),

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user)

):

    session = db.query(models.AdvisorySession).filter(

        models.AdvisorySession.id == session_id,

        models.AdvisorySession.user_id == current_user.id

    ).first()



    if not session:

        raise HTTPException(status_code=403, detail="Not authorized to access this session")



    user_msg_db = models.AdvisoryMessage(

        session_id=session_id,

        role="user",

        content=user_message

    )

    db.add(user_msg_db)

    db.commit()



    cockpit_service.log_prompt(

        db, current_user.id, current_user.company_id, agent_id, user_message

    )



    try:

        chat_req = schemas.ChatRequest(

            user_message=user_message,

            session_id=session_id,

            company_id=str(current_user.company_id) if current_user.company_id else None,

            agent_id=agent_id,

        )

        user_context = {

            "user_id": str(current_user.id),

            "company_id": str(current_user.company_id) if current_user.company_id else None

        }

        agent_resp = await agent.run_agent(chat_req, user_context)

        assistant_msg_db = models.AdvisoryMessage(

            session_id=session_id,

            role="assistant",

            content=agent_resp.response,

            referenced_sources=agent_resp.sources

        )

        db.add(assistant_msg_db)

        db.commit()

    except Exception as e:

        print(f"Error calling agent: {e}")

        db.add(models.AdvisoryMessage(

            session_id=session_id,

            role="assistant",

            content="Desculpe, ocorreu um erro ao processar sua solicitação."

        ))

        db.commit()



    return RedirectResponse(

        url=f"/api/v1/advisory/dashboard?session_id={session_id}&agent={agent_id}",

        status_code=303,

    )



@router.post("/chat/ask", response_model=schemas.AdvisoryResponse)

async def ask_advisor(request: schemas.ChatRequest):

    return await agent.run_agent(request)



@router.get("/knowledge", response_model=list[schemas.KnowledgeBaseItemOut])

def get_knowledge_base(

    skip: int = 0,

    limit: int = 100,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    q = db.query(models.AdvisoryKnowledgeBase)

    if current_user.company_id:

        q = q.filter(models.AdvisoryKnowledgeBase.company_id == current_user.company_id)

    return q.offset(skip).limit(limit).all()



@router.post("/knowledge", response_model=schemas.KnowledgeBaseItemOut)

def add_knowledge_item(

    item: schemas.KnowledgeBaseItemCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    company_id = item.company_id or current_user.company_id

    db_item = models.AdvisoryKnowledgeBase(

        content=item.content,

        source_title=item.source_title,

        source_type=item.source_type,

        company_id=company_id,

    )

    db.add(db_item)

    db.commit()

    db.refresh(db_item)

    return db_item


