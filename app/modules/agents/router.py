from typing import Optional, List

from datetime import datetime

import uuid



from fastapi import APIRouter, Request, Depends, HTTPException, Form

from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session



from app.core.database import get_db

from app.core import security

from app.core.models import User, Company

from app.core.tenant import get_company_id

from app.modules.advisory import schemas as advisory_schemas

from app.modules.agents import manager, models, registry, schemas, action_executor



router = APIRouter()

templates = Jinja2Templates(directory="app/templates")





def _filter_by_tenant(query, company_id):

    if company_id:

        return query.filter(models.AgentAction.company_id == company_id)

    return query





@router.get("/command-center")

def command_center(

    request: Request,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    company_id = current_user.company_id

    pending_q = db.query(models.AgentAction).filter(models.AgentAction.status == "pending")

    runs_q = db.query(models.AgentOrchestrationRun)

    if company_id:

        pending_q = pending_q.filter(models.AgentAction.company_id == company_id)

        runs_q = runs_q.filter(

            (models.AgentOrchestrationRun.company_id == company_id)

            | (models.AgentOrchestrationRun.company_id.is_(None))

        )



    pending = pending_q.order_by(models.AgentAction.created_at.desc()).limit(20).all()

    recent_runs = runs_q.order_by(models.AgentOrchestrationRun.created_at.desc()).limit(10).all()

    companies = db.query(Company).all()



    return templates.TemplateResponse("dashboard/command_center.html", {

        "request": request,

        "pending_actions": pending,

        "recent_runs": recent_runs,

        "agents": registry.list_agents(),

        "companies": companies,

        "current_company_id": str(company_id) if company_id else "",

        "persona_labels": __import__(

            "app.modules.advisory.prompts", fromlist=["PERSONA_LABELS"]

        ).PERSONA_LABELS,

    })





@router.post("/orchestrate", response_model=advisory_schemas.OrchestrationResponse)

async def orchestrate(

    body: advisory_schemas.OrchestrationRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    if body.company_ids and len(body.company_ids) > 1:

        raise HTTPException(

            status_code=400,

            detail="Use POST /orchestrate/multi for multiple companies",

        )

    company_id = body.company_id or (

        str(current_user.company_id) if current_user.company_id else None

    )

    return await manager.run_orchestration(

        objective=body.objective,

        company_id=company_id,

        agents=body.agents,

        db=db,

        user_id=str(current_user.id),

    )





@router.post("/orchestrate/multi", response_model=advisory_schemas.MultiOrchestrationResponse)

async def orchestrate_multi(

    body: advisory_schemas.OrchestrationRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    company_ids = body.company_ids or []

    if not company_ids and body.company_id:

        company_ids = [body.company_id]

    if not company_ids and current_user.company_id:

        company_ids = [str(current_user.company_id)]

    if len(company_ids) < 2:

        raise HTTPException(status_code=400, detail="Provide at least 2 company_ids for multi-startup mode")

    return await manager.run_multi_orchestration(

        objective=body.objective,

        company_ids=company_ids,

        agents=body.agents,

        db=db,

        user_id=str(current_user.id),

    )





@router.post("/command-center/run", response_class=RedirectResponse)

async def run_from_ui(

    objective: str = Form(...),

    mode: str = Form("single"),

    company_ids: Optional[List[str]] = Form(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    if mode == "multi" and company_ids and len(company_ids) >= 2:

        await manager.run_multi_orchestration(

            objective=objective,

            company_ids=company_ids,

            db=db,

            user_id=str(current_user.id),

        )

    else:

        company_id = str(current_user.company_id) if current_user.company_id else None

        await manager.run_orchestration(

            objective=objective,

            company_id=company_id,

            db=db,

            user_id=str(current_user.id),

        )

    return RedirectResponse(url="/api/v1/agents/command-center", status_code=303)





@router.get("/actions/pending", response_model=List[schemas.AgentActionOut])

def list_pending_actions(

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    q = db.query(models.AgentAction).filter(models.AgentAction.status == "pending")

    if current_user.company_id:

        q = q.filter(models.AgentAction.company_id == current_user.company_id)

    return q.order_by(models.AgentAction.created_at.desc()).all()





def _approve_and_execute(db: Session, action: models.AgentAction) -> dict:

    action.status = "approved"

    action.resolved_at = datetime.utcnow()

    result = action_executor.execute_action(db, action)

    action.payload = {**(action.payload or {}), "execution_result": result}

    db.commit()

    return result





@router.post("/actions/{action_id}/resolve")

def resolve_action(

    action_id: uuid.UUID,

    body: schemas.AgentActionResolve,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    if body.status not in ("approved", "rejected"):

        raise HTTPException(status_code=400, detail="status must be approved or rejected")



    action = db.query(models.AgentAction).filter(models.AgentAction.id == action_id).first()

    if not action:

        raise HTTPException(status_code=404, detail="Action not found")



    action.resolved_by = current_user.id

    if body.status == "approved":

        result = _approve_and_execute(db, action)

        return {"id": str(action.id), "status": "approved", "execution": result}



    action.status = "rejected"

    action.resolved_at = datetime.utcnow()

    db.commit()

    return {"id": str(action.id), "status": "rejected"}





@router.post("/actions/{action_id}/approve", response_class=RedirectResponse)

def approve_action_ui(

    action_id: uuid.UUID,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    action = db.query(models.AgentAction).filter(models.AgentAction.id == action_id).first()

    if action:

        action.resolved_by = current_user.id

        _approve_and_execute(db, action)

    return RedirectResponse(url="/api/v1/agents/command-center", status_code=303)





@router.post("/actions/{action_id}/reject", response_class=RedirectResponse)

def reject_action_ui(

    action_id: uuid.UUID,

    db: Session = Depends(get_db),

    current_user: User = Depends(security.get_current_user),

):

    action = db.query(models.AgentAction).filter(models.AgentAction.id == action_id).first()

    if action:

        action.status = "rejected"

        action.resolved_at = datetime.utcnow()

        action.resolved_by = current_user.id

        db.commit()

    return RedirectResponse(url="/api/v1/agents/command-center", status_code=303)





@router.get("/registry")

def get_registry():

    return registry.list_agents()


