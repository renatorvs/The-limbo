"""Agrega KPIs live + metas MVP e calcula status para ajuste rápido."""

import json
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import Company, AnalyticsSaasMetricsDaily
from app.modules.advisory import tools
from app.modules.cockpit import models, schemas
from app.modules.cockpit.kpi_catalog import MVP_KPI_CATALOG, DOMAIN_LABELS
from sqlalchemy import desc


def _status(current: Optional[float], target: float, direction: str, critical_below: Optional[float]) -> str:
    if current is None:
        return "no_data"
    if direction == "above":
        if current >= target:
            return "on_track"
        if critical_below is not None and current < critical_below:
            return "off_track"
        return "at_risk"
    else:  # below
        if current <= target:
            return "on_track"
        if critical_below is not None and current > critical_below:
            return "off_track"
        return "at_risk"


def _gap(current: Optional[float], target: float) -> Optional[float]:
    if current is None or target == 0:
        return None
    return round(((current - target) / target) * 100, 1)


def _fetch_live_values(db: Session, company_id: UUID) -> Dict[str, Optional[float]]:
    """Pull KPIs: relatório de app (primário) + banco Limbo (secundário/fallback)."""
    from app.modules.reports import service as report_service

    values: Dict[str, Optional[float]] = {}

    report_metrics = report_service.get_latest_metrics(db, company_id)
    if report_metrics:
        values.update(report_metrics)

    cid = str(company_id)

    def _fill(key: str, val):
        if values.get(key) is None and val is not None:
            values[key] = val

    fin = json.loads(tools._get_financial_stats(cid))
    _fill("runway_months", fin.get("runway_months"))
    _fill("monthly_burn", fin.get("monthly_burn_rate"))
    _fill("total_balance", fin.get("total_balance"))

    growth = json.loads(tools._get_growth_metrics(cid))
    _fill("mrr", growth.get("mrr"))
    _fill("cac", growth.get("cac"))
    ltv_cac = (
        round(growth["ltv"] / growth["cac"], 2)
        if growth.get("ltv") and growth.get("cac") and growth["cac"] > 0
        else None
    )
    _fill("ltv_cac_ratio", ltv_cac)
    _fill("trial_conversion", growth.get("trial_conversion_rate"))

    funnel = json.loads(tools._get_funnel_snapshot(cid))
    if isinstance(funnel, dict):
        _fill("leads", funnel.get("leads"))

    eng = json.loads(tools._get_engineering_metrics(cid))
    _fill("bugs_open", eng.get("bugs_open"))
    _fill("uptime", eng.get("uptime"))

    cs = json.loads(tools._get_cs_dashboard(cid))
    _fill("nps_score", cs.get("nps_score"))
    _fill("active_customers", cs.get("active_customers"))
    _fill("open_tickets", cs.get("open_tickets"))

    latest = (
        db.query(AnalyticsSaasMetricsDaily)
        .filter(AnalyticsSaasMetricsDaily.company_id == company_id)
        .order_by(desc(AnalyticsSaasMetricsDaily.reference_date))
        .first()
    )
    if latest:
        values["dau"] = float(latest.dau) if latest.dau else values.get("dau")
        values["activation_rate"] = float(latest.activation_rate_percent) if latest.activation_rate_percent else None
        values["churn_rate"] = float(latest.churn_rate_percent) if latest.churn_rate_percent else None
        if latest.churn_rate_percent is not None:
            values["churn_rate"] = float(latest.churn_rate_percent)

    return values


def _get_target(db: Session, company_id: UUID, domain: str, metric_key: str, default: float) -> float:
    goal = (
        db.query(models.MvpGoal)
        .filter(
            models.MvpGoal.company_id == company_id,
            models.MvpGoal.domain == domain,
            models.MvpGoal.metric_key == metric_key,
        )
        .first()
    )
    return float(goal.target_value) if goal else default


def get_mvp_dashboard(db: Session, company_id: UUID) -> schemas.MvpDashboard:
    company = db.query(Company).filter(Company.id == company_id).first()
    live = _fetch_live_values(db, company_id)
    domains_out = []
    total_at_risk = 0
    total_off = 0

    for domain, catalog in MVP_KPI_CATALOG.items():
        kpis = []
        on_track = at_risk = 0
        for item in catalog:
            target = _get_target(db, company_id, domain, item["key"], item["default_target"])
            current = live.get(item["key"])
            status = _status(current, target, item["direction"], item.get("critical_below"))
            if status == "on_track":
                on_track += 1
            elif status == "at_risk":
                at_risk += 1
                total_at_risk += 1
            elif status == "off_track":
                total_off += 1
            kpis.append(schemas.MvpKpiItem(
                key=item["key"],
                label=item["label"],
                unit=item["unit"],
                current_value=current,
                target_value=target,
                status=status,
                direction=item["direction"],
                gap_percent=_gap(current, target),
            ))
        domains_out.append(schemas.MvpDomainDashboard(
            domain=domain,
            label=DOMAIN_LABELS.get(domain, domain),
            kpis=kpis,
            on_track_count=on_track,
            at_risk_count=at_risk,
        ))

    if total_off > 0:
        health = "red"
    elif total_at_risk > 2:
        health = "yellow"
    else:
        health = "green"

    return schemas.MvpDashboard(
        company_id=str(company_id),
        company_name=company.name if company else None,
        domains=domains_out,
        overall_health=health,
    )


def upsert_goal(db: Session, company_id: UUID, data: schemas.MvpGoalUpdate) -> models.MvpGoal:
    goal = (
        db.query(models.MvpGoal)
        .filter(
            models.MvpGoal.company_id == company_id,
            models.MvpGoal.domain == data.domain,
            models.MvpGoal.metric_key == data.metric_key,
        )
        .first()
    )
    if goal:
        goal.target_value = data.target_value
        goal.deadline = data.deadline
        goal.notes = data.notes
    else:
        goal = models.MvpGoal(
            company_id=company_id,
            domain=data.domain,
            metric_key=data.metric_key,
            target_value=data.target_value,
            deadline=data.deadline,
            notes=data.notes,
        )
        db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def log_prompt(db: Session, user_id: UUID, company_id: Optional[UUID], agent_id: str, prompt_text: str):
    entry = models.PromptHistory(
        user_id=user_id,
        company_id=company_id,
        agent_id=agent_id,
        prompt_text=prompt_text,
    )
    db.add(entry)
    db.commit()


def get_history(db: Session, user_id: UUID, agent_id: Optional[str] = None, limit: int = 20):
    q = db.query(models.PromptHistory).filter(models.PromptHistory.user_id == user_id)
    if agent_id:
        q = q.filter(models.PromptHistory.agent_id == agent_id)
    return q.order_by(models.PromptHistory.created_at.desc()).limit(limit).all()


def add_favorite(db: Session, user_id: UUID, data: schemas.PromptFavoriteCreate) -> models.PromptFavorite:
    fav = models.PromptFavorite(
        user_id=user_id,
        agent_id=data.agent_id,
        label=data.label,
        prompt_text=data.prompt_text,
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


def get_favorites(db: Session, user_id: UUID, agent_id: Optional[str] = None):
    q = db.query(models.PromptFavorite).filter(models.PromptFavorite.user_id == user_id)
    if agent_id:
        q = q.filter(models.PromptFavorite.agent_id == agent_id)
    return q.order_by(models.PromptFavorite.created_at.desc()).all()


def delete_favorite(db: Session, user_id: UUID, favorite_id: UUID) -> bool:
    fav = (
        db.query(models.PromptFavorite)
        .filter(models.PromptFavorite.id == favorite_id, models.PromptFavorite.user_id == user_id)
        .first()
    )
    if not fav:
        return False
    db.delete(fav)
    db.commit()
    return True
