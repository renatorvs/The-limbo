from sqlalchemy.orm import Session
from . import models, schemas

from sqlalchemy import desc
from app.core.models import AnalyticsSaasMetricsDaily
from uuid import UUID
from typing import Optional

def create_campaign(db: Session, campaign: schemas.CampaignCreate):
    db_campaign = models.Campaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def get_campaigns(db: Session, skip: int = 0, limit: int = 100, company_id: Optional[UUID] = None):
    q = db.query(models.Campaign).filter(models.Campaign.status == 'Active')
    if company_id:
        q = q.filter(models.Campaign.company_id == company_id)
    return q.offset(skip).limit(limit).all()

def create_funnel_snapshot(db: Session, snapshot: schemas.FunnelSnapshotCreate):
    db_obj = models.FunnelSnapshot(**snapshot.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_latest_funnel(db: Session, company_id: Optional[UUID] = None):
    q = db.query(models.FunnelSnapshot)
    if company_id:
        q = q.filter(models.FunnelSnapshot.company_id == company_id)
    return q.order_by(desc(models.FunnelSnapshot.date)).first()

def get_metrics(db: Session, company_id: Optional[UUID] = None):
    q = db.query(AnalyticsSaasMetricsDaily)
    if company_id:
        q = q.filter(AnalyticsSaasMetricsDaily.company_id == company_id)
    latest_metrics = q.order_by(desc(AnalyticsSaasMetricsDaily.reference_date)).first()
    
    if latest_metrics:
        return schemas.GrowthDashboardStats(
            arr=float(latest_metrics.arr or 0.0),
            ltv=float(latest_metrics.ltv or 0.0),
            churn_rate=float(latest_metrics.churn_rate_percent or 0.0),
            cac=float(latest_metrics.cac or 0.0),
            quick_ratio=2.4, # Mock for now, requires complex calc
            nps=int(latest_metrics.nps_score or 0),
            star_metric=1250 # Mock
        )
    else:
        # Return zeros if no data
        return schemas.GrowthDashboardStats(
            arr=0.0, ltv=0.0, churn_rate=0.0, cac=0.0, quick_ratio=0.0, nps=0, star_metric=0
        )
