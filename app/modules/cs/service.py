from sqlalchemy.orm import Session
from sqlalchemy import func, case
from . import models, schemas
from datetime import datetime

def get_dashboard_stats(db: Session) -> schemas.DashboardStats:
    # 1. NPS Calculation
    nps_counts = db.query(
        func.count(models.NpsSurvey.id).label("total"),
        func.sum(case((models.NpsSurvey.score >= 9, 1), else_=0)).label("promoters"),
        func.sum(case((models.NpsSurvey.score <= 6, 1), else_=0)).label("detractors"),
        func.sum(case(((models.NpsSurvey.score >= 7) & (models.NpsSurvey.score <= 8), 1), else_=0)).label("neutrals")
    ).first()

    total_surveys = nps_counts.total or 0
    promoters = nps_counts.promoters or 0
    detractors = nps_counts.detractors or 0
    neutrals = nps_counts.neutrals or 0

    if total_surveys > 0:
        nps_score = ((promoters - detractors) / total_surveys) * 100
        nps_promoters_pct = (promoters / total_surveys) * 100
        nps_detractors_pct = (detractors / total_surveys) * 100
        nps_neutrals_pct = (neutrals / total_surveys) * 100
    else:
        nps_score = 0
        nps_promoters_pct = 0
        nps_detractors_pct = 0
        nps_neutrals_pct = 0

    # 2. Financials (MRR & Active Customers)
    financials = db.query(
        func.sum(models.Customer.mrr_value).label("total_mrr"),
        func.count(models.Customer.id).label("active_customers")
    ).filter(models.Customer.churned_at == None).first()

    total_mrr = financials.total_mrr or 0.0
    active_customers = financials.active_customers or 0

    # 3. Churn Rate (Simplified: Churned / (Active + Churned)) - This is a rough approximation
    churned_count = db.query(func.count(models.Customer.id)).filter(models.Customer.churned_at != None).scalar() or 0
    total_customers_ever = active_customers + churned_count
    
    churn_rate = 0.0
    if total_customers_ever > 0:
        churn_rate = (churned_count / total_customers_ever) * 100

    # Mock Expansion Revenue (Need transaction data for real calc)
    expansion_revenue = total_mrr * 0.15 # 15% of MRR as mockup

    return schemas.DashboardStats(
        churn_rate=round(churn_rate, 2),
        nps_score=int(nps_score),
        expansion_revenue=round(float(expansion_revenue), 2),
        total_mrr=round(float(total_mrr), 2),
        active_customers=active_customers,
        nps_promoters_pct=int(nps_promoters_pct),
        nps_neutrals_pct=int(nps_neutrals_pct),
        nps_detractors_pct=int(nps_detractors_pct)
    )

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).order_by(models.Customer.health_score.asc()).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_obj = models.Customer(**customer.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
