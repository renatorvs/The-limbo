from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import schemas, service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def view_dashboard(request: Request, db: Session = Depends(get_db)):
    metrics = service.get_metrics(db)
    funnel = service.get_latest_funnel(db)
    campaigns = service.get_campaigns(db)
    
    # Format funnel data for Chart.js
    funnel_data = {
        "visitors": funnel.visitors if funnel else 0,
        "leads": funnel.leads if funnel else 0,
        "customers": funnel.customers if funnel else 0
    }

    return templates.TemplateResponse("dashboard/growth.html", {
        "request": request,
        "metrics": metrics,
        "funnel": funnel,
        "funnel_data": funnel_data,
        "campaigns": campaigns
    })

@router.post("/campaign", response_model=schemas.CampaignOut)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    return service.create_campaign(db=db, campaign=campaign)

@router.get("/campaigns", response_model=list[schemas.CampaignOut])
def get_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_campaigns(db, skip, limit)

@router.post("/funnel", response_model=schemas.FunnelSnapshotOut)
def create_funnel_snapshot(snapshot: schemas.FunnelSnapshotCreate, db: Session = Depends(get_db)):
    return service.create_funnel_snapshot(db, snapshot)

@router.get("/metrics")
def get_growth_metrics():
    return service.get_metrics()
