from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import security
from app.core.models import User
from app.core.tenant import require_company_id
from app.modules.cockpit import service, schemas, prompt_library
from app.modules.cockpit.kpi_catalog import DOMAIN_LABELS
from app.modules.advisory import prompts

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def mvp_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
    current_user: User = Depends(security.get_current_user),
):
    dashboard = service.get_mvp_dashboard(db, company_id)
    all_suggestions = prompt_library.get_all_by_domain()
    return templates.TemplateResponse("dashboard/cockpit.html", {
        "request": request,
        "dashboard": dashboard,
        "domain_labels": DOMAIN_LABELS,
        "persona_labels": prompts.PERSONA_LABELS,
        "all_suggestions": all_suggestions,
    })


@router.post("/goals/quick-update", response_class=RedirectResponse)
def quick_update_goal(
    domain: str = Form(...),
    metric_key: str = Form(...),
    target_value: float = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    service.upsert_goal(db, company_id, schemas.MvpGoalUpdate(
        domain=domain,
        metric_key=metric_key,
        target_value=target_value,
        notes=notes or None,
    ))
    return RedirectResponse(url="/api/v1/cockpit/dashboard", status_code=303)


@router.get("/api/dashboard", response_model=schemas.MvpDashboard)
def get_dashboard_api(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    return service.get_mvp_dashboard(db, company_id)


@router.get("/prompts/suggestions/{agent_id}", response_model=List[schemas.PromptSuggestionOut])
def get_suggestions(agent_id: str):
    return prompt_library.get_suggestions(agent_id)


@router.get("/prompts/history", response_model=List[schemas.PromptHistoryOut])
def get_prompt_history(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    return service.get_history(db, current_user.id, agent_id)


@router.get("/prompts/favorites", response_model=List[schemas.PromptFavoriteOut])
def get_favorites(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    return service.get_favorites(db, current_user.id, agent_id)


@router.post("/prompts/favorites", response_model=schemas.PromptFavoriteOut)
def create_favorite(
    body: schemas.PromptFavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    return service.add_favorite(db, current_user.id, body)


@router.post("/prompts/favorites/form", response_class=RedirectResponse)
def create_favorite_form(
    agent_id: str = Form(...),
    label: str = Form(...),
    prompt_text: str = Form(...),
    redirect: str = Form("/api/v1/advisory/dashboard"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    service.add_favorite(db, current_user.id, schemas.PromptFavoriteCreate(
        agent_id=agent_id, label=label, prompt_text=prompt_text,
    ))
    return RedirectResponse(url=redirect, status_code=303)


@router.post("/prompts/favorites/{favorite_id}/delete", response_class=RedirectResponse)
def delete_favorite_form(
    favorite_id: UUID,
    redirect: str = Form("/api/v1/advisory/dashboard"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    service.delete_favorite(db, current_user.id, favorite_id)
    return RedirectResponse(url=redirect, status_code=303)


@router.delete("/prompts/favorites/{favorite_id}")
def delete_favorite_api(
    favorite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user),
):
    if not service.delete_favorite(db, current_user.id, favorite_id):
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"deleted": True}
