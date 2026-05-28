"""Hub service: INPUT → process → OUTPUT for Sofia Education IA & BodyVision.IA."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import Company
from app.modules.hub import models, schemas, products
from app.modules.reports import service as report_service, schemas as report_schemas
from app.modules.cockpit import service as cockpit_service
from app.modules.agents import models as agent_models


def ensure_products(db: Session) -> dict[str, UUID]:
    """Garante que Sofia e BodyVision existem no banco. Retorna app_key → company_id."""
    mapping = {}
    for app_key, cfg in products.PRODUCTS.items():
        co = db.query(Company).filter(Company.app_key == app_key).first()
        if not co:
            co = db.query(Company).filter(Company.name == cfg["name"]).first()
        if not co:
            co = Company(name=cfg["name"], industry=cfg["industry"], app_key=app_key)
            db.add(co)
            db.flush()
        else:
            co.app_key = app_key
            co.industry = cfg["industry"]
        mapping[app_key] = co.id
    db.commit()
    return mapping


def get_company_by_app_key(db: Session, app_key: str) -> Optional[Company]:
    cfg = products.get_product(app_key)
    if not cfg:
        return None
    co = db.query(Company).filter(Company.app_key == app_key).first()
    if not co:
        ensure_products(db)
        co = db.query(Company).filter(Company.app_key == app_key).first()
    return co


def process_input(
    db: Session,
    app_key: str,
    report: report_schemas.AppReportIngest,
) -> schemas.HubInputResponse:
    """INPUT: app envia relatório → Limbo ingere → gera OUTPUT."""
    company = get_company_by_app_key(db, app_key)
    if not company:
        raise ValueError(f"Produto '{app_key}' não configurado.")

    cfg = products.get_product(app_key)
    report.company_ref.id = str(company.id)
    report.source_app = cfg["source_app"]

    ingest_result = report_service.ingest_report(db, report)
    output = generate_output(db, app_key, company.id, ingest_result.report_id)

    return schemas.HubInputResponse(
        app_key=app_key,
        report_id=ingest_result.report_id,
        output_id=output.id,
        message=f"INPUT recebido de {cfg['name']}. OUTPUT disponível em /hub/{app_key}/output",
    )


def generate_output(
    db: Session,
    app_key: str,
    company_id: UUID,
    source_report_id: Optional[UUID] = None,
) -> models.LimboOutput:
    """Gera pacote OUTPUT para a app consumir."""
    cfg = products.get_product(app_key)
    report = report_service.get_latest_report(db, company_id)
    dashboard = cockpit_service.get_mvp_dashboard(db, company_id)

    kpi_alerts = []
    recommendations = []
    goal_adjustments = []

    for domain in dashboard.domains:
        for kpi in domain.kpis:
            if kpi.status in ("at_risk", "off_track"):
                kpi_alerts.append({
                    "domain": domain.domain,
                    "metric": kpi.key,
                    "label": kpi.label,
                    "current": kpi.current_value,
                    "target": kpi.target_value,
                    "status": kpi.status,
                    "gap_percent": kpi.gap_percent,
                })
                if kpi.direction == "above" and kpi.current_value is not None:
                    goal_adjustments.append({
                        "domain": domain.domain,
                        "metric_key": kpi.key,
                        "suggestion": f"Ajustar meta de {kpi.label} ou acelerar ações corretivas",
                        "current": kpi.current_value,
                        "target": kpi.target_value,
                    })

    if report and report.domain_narratives:
        for domain, narrative in report.domain_narratives.items():
            recommendations.extend(
                f"[{domain.upper()}] {r}" for r in narrative.get("recommendations", [])
            )

    approved = (
        db.query(agent_models.AgentAction)
        .filter(
            agent_models.AgentAction.company_id == company_id,
            agent_models.AgentAction.status == "approved",
        )
        .order_by(desc(agent_models.AgentAction.resolved_at))
        .limit(10)
        .all()
    )
    pending = (
        db.query(agent_models.AgentAction)
        .filter(
            agent_models.AgentAction.company_id == company_id,
            agent_models.AgentAction.status == "pending",
        )
        .order_by(desc(agent_models.AgentAction.created_at))
        .limit(10)
        .all()
    )

    briefing = report.executive_summary if report else f"Aguardando primeiro INPUT de {cfg['name']}."
    if kpi_alerts:
        briefing += f"\n\n⚠ {len(kpi_alerts)} KPI(s) fora do trilho — ver kpi_alerts."

    payload = {
        "app_key": app_key,
        "product_name": cfg["name"],
        "briefing": briefing,
        "kpi_alerts": kpi_alerts,
        "recommendations": recommendations[:15],
        "approved_actions": [
            {"id": str(a.id), "type": a.action_type, "description": a.description, "payload": a.payload}
            for a in approved
        ],
        "pending_approval": [
            {"id": str(a.id), "type": a.action_type, "description": a.description}
            for a in pending
        ],
        "goal_adjustments": goal_adjustments,
        "metrics_snapshot": report.parsed_metrics if report else {},
        "focus_priorities": cfg["mvp_priorities"],
    }

    db.query(models.LimboOutput).filter(
        models.LimboOutput.app_key == app_key,
        models.LimboOutput.is_active == True,
    ).update({"is_active": False})

    output = models.LimboOutput(
        company_id=company_id,
        app_key=app_key,
        source_report_id=source_report_id or (report.id if report else None),
        briefing=briefing,
        payload=payload,
        is_active=True,
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output


def get_output(db: Session, app_key: str, mark_consumed: bool = False) -> Optional[schemas.HubOutput]:
    """OUTPUT: app busca decisões e recomendações do Limbo."""
    company = get_company_by_app_key(db, app_key)
    if not company:
        return None

    row = (
        db.query(models.LimboOutput)
        .filter(models.LimboOutput.app_key == app_key, models.LimboOutput.is_active == True)
        .order_by(desc(models.LimboOutput.created_at))
        .first()
    )
    if not row:
        row = generate_output(db, app_key, company.id)

    cfg = products.get_product(app_key)
    if mark_consumed:
        row.consumed_at = datetime.utcnow()
        db.commit()

    p = row.payload
    return schemas.HubOutput(
        app_key=app_key,
        product_name=cfg["name"],
        generated_at=row.created_at,
        briefing=p["briefing"],
        kpi_alerts=[schemas.KpiAlert(**a) for a in p.get("kpi_alerts", [])],
        recommendations=p.get("recommendations", []),
        approved_actions=p.get("approved_actions", []),
        pending_approval=p.get("pending_approval", []),
        goal_adjustments=p.get("goal_adjustments", []),
        metrics_snapshot=p.get("metrics_snapshot", {}),
        output_id=row.id,
    )


def get_products_status(db: Session) -> List[schemas.ProductStatus]:
    ensure_products(db)
    statuses = []
    for app_key in products.PRODUCTS:
        co = get_company_by_app_key(db, app_key)
        if not co:
            continue
        report = report_service.get_latest_report(db, co.id)
        output = (
            db.query(models.LimboOutput)
            .filter(models.LimboOutput.app_key == app_key, models.LimboOutput.is_active == True)
            .first()
        )
        dash = cockpit_service.get_mvp_dashboard(db, co.id)
        statuses.append(schemas.ProductStatus(
            app_key=app_key,
            name=products.PRODUCTS[app_key]["name"],
            company_id=str(co.id),
            last_input_at=report.ingested_at if report else None,
            last_output_at=output.created_at if output else None,
            overall_health=dash.overall_health,
            has_pending_output=output is not None and output.consumed_at is None,
        ))
    return statuses
