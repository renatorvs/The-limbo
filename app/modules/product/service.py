from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from uuid import UUID

def get_roadmap_items(db: Session, company_id: UUID = None):
    query = db.query(models.RoadmapItem)
    if company_id:
        query = query.filter(models.RoadmapItem.company_id == company_id)
    return query.all()

def create_roadmap_item(db: Session, item: schemas.RoadmapItemCreate):
    db_item = models.RoadmapItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_engineering_metrics(db: Session, company_id: UUID = None):
    # This is a simplified version. In a real app, you'd fetch the LATEST value for each metric name.
    # For now, we'll just return all or filter by latest date.
    # A better approach might be to define specific metrics we care about.
    
    metrics = {}
    # Example: specific queries for known metrics
    # Uptime
    uptime = db.query(models.EngineeringMetrics).filter(models.EngineeringMetrics.metric_name == 'uptime').order_by(models.EngineeringMetrics.measured_at.desc()).first()
    metrics['uptime'] = float(uptime.value) if uptime else 99.9
    
    # Bugs
    bugs = db.query(models.EngineeringMetrics).filter(models.EngineeringMetrics.metric_name == 'bugs_open').order_by(models.EngineeringMetrics.measured_at.desc()).first()
    metrics['bugs_open'] = int(bugs.value) if bugs else 0
    
    # Deploy Frequency
    deploy_freq = db.query(models.EngineeringMetrics).filter(models.EngineeringMetrics.metric_name == 'deploy_frequency').order_by(models.EngineeringMetrics.measured_at.desc()).first()
    metrics['deploy_frequency'] = float(deploy_freq.value) if deploy_freq else 0.0
    
    return metrics
