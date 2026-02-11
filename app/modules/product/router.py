from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import schemas, models, service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def view_dashboard(request: Request, db: Session = Depends(get_db)):
    # Fetch all items (in a multi-tenant app, we'd filter by company from user context)
    # For now, user context is not fully wired, so we fetch all or a specific company if we knew it
    # We'll just fetch all for the demo
    all_items = service.get_roadmap_items(db)
    metrics = service.get_engineering_metrics(db)
    
    # Group items by status
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
        "metrics": metrics
    })

@router.post("/roadmap", response_model=schemas.RoadmapItemOut)
def create_roadmap_item(item: schemas.RoadmapItemCreate, db: Session = Depends(get_db)):
    return service.create_roadmap_item(db, item)

@router.get("/roadmap", response_model=list[schemas.RoadmapItemOut])
def get_roadmap(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Use service in future, for now direct query is fine for API, but better to be consistent
    return service.get_roadmap_items(db)

@router.post("/active-users", response_model=schemas.EngineeringMetricsOut)
def record_engineering_metric(metric: schemas.EngineeringMetricsCreate, db: Session = Depends(get_db)):
    db_metric = models.EngineeringMetrics(**metric.model_dump())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric
