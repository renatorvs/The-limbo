from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.tenant import require_company_id
from . import schemas, models, service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def view_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    all_items = service.get_roadmap_items(db, company_id=company_id)
    metrics = service.get_engineering_metrics(db, company_id=company_id)

    backlog = [item for item in all_items if item.status == 'backlog']
    in_progress = [item for item in all_items if item.status == 'in_progress']
    testing = [item for item in all_items if item.status == 'testing']
    released = [item for item in all_items if item.status == 'released']

    return templates.TemplateResponse("dashboard/product.html", {
        "request": request,
        "backlog_items": backlog,
        "in_progress_items": in_progress,
        "testing_items": testing,
        "released_items": released,
        "metrics": metrics,
    })

@router.post("/roadmap", response_model=schemas.RoadmapItemOut)
def create_roadmap_item(
    item: schemas.RoadmapItemCreate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    if not item.company_id:
        item.company_id = company_id
    return service.create_roadmap_item(db, item)

@router.get("/roadmap", response_model=list[schemas.RoadmapItemOut])
def get_roadmap(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    return service.get_roadmap_items(db, company_id=company_id)

@router.post("/active-users", response_model=schemas.EngineeringMetricsOut)
def record_engineering_metric(
    metric: schemas.EngineeringMetricsCreate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    data = metric.model_dump()
    if not data.get("company_id"):
        data["company_id"] = company_id
    db_metric = models.EngineeringMetrics(**data)
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric
