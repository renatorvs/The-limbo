"""Gera relatórios MVP exportáveis — HTML, Markdown, JSON — para uso fora do Limbo."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import Company
from app.modules.cockpit import service, models
from app.modules.cockpit.kpi_catalog import MVP_KPI_CATALOG, DOMAIN_LABELS
from app.modules.agents import models as agent_models

REPORT_VERSION = "1.0"

STATUS_LABELS = {
    "on_track": "No trilho",
    "at_risk": "Em risco",
    "off_track": "Fora da meta",
    "no_data": "Sem dados",
}

HEALTH_LABELS = {
    "green": "Saudável",
    "yellow": "Atenção",
    "red": "Crítico",
}


def _get_goals_map(db: Session, company_id: UUID) -> dict:
    goals = db.query(models.MvpGoal).filter(models.MvpGoal.company_id == company_id).all()
    return {(g.domain, g.metric_key): g for g in goals}


def _external_template() -> dict:
    """Schema vazio para preencher quando dados estão em outro ambiente."""
    template = {"company": {"name": "", "industry": "", "notes": ""}, "domains": {}}
    for domain, catalog in MVP_KPI_CATALOG.items():
        template["domains"][domain] = {
            "label": DOMAIN_LABELS.get(domain, domain),
            "metrics": {
                item["key"]: {
                    "label": item["label"],
                    "current_value": None,
                    "target_value": item["default_target"],
                    "unit": item["unit"],
                }
                for item in catalog
            },
        }
    return template


def build_company_report(db: Session, company_id: UUID) -> dict:
    company = db.query(Company).filter(Company.id == company_id).first()
    dashboard = service.get_mvp_dashboard(db, company_id)
    goals_map = _get_goals_map(db, company_id)

    domains = []
    gaps = []
    at_risk_items = []

    for domain in dashboard.domains:
        metrics = []
        for kpi in domain.kpis:
            goal = goals_map.get((domain.domain, kpi.key))
            entry = {
                "key": kpi.key,
                "label": kpi.label,
                "unit": kpi.unit,
                "current_value": kpi.current_value,
                "target_value": kpi.target_value,
                "gap_percent": kpi.gap_percent,
                "status": kpi.status,
                "status_label": STATUS_LABELS.get(kpi.status, kpi.status),
                "direction": kpi.direction,
                "notes": goal.notes if goal else None,
                "deadline": str(goal.deadline) if goal and goal.deadline else None,
            }
            metrics.append(entry)
            if kpi.status == "no_data":
                gaps.append(f"{domain.label} → {kpi.label}")
            elif kpi.status in ("at_risk", "off_track"):
                at_risk_items.append({
                    "domain": domain.label,
                    "metric": kpi.label,
                    "current": kpi.current_value,
                    "target": kpi.target_value,
                    "status": kpi.status,
                })
        domains.append({
            "domain": domain.domain,
            "label": domain.label,
            "on_track_count": domain.on_track_count,
            "at_risk_count": domain.at_risk_count,
            "metrics": metrics,
        })

    recent_runs = (
        db.query(agent_models.AgentOrchestrationRun)
        .filter(agent_models.AgentOrchestrationRun.company_id == company_id)
        .order_by(desc(agent_models.AgentOrchestrationRun.created_at))
        .limit(3)
        .all()
    )
    orchestrations = [
        {
            "objective": r.objective,
            "synthesis": r.synthesis,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_runs
    ]

    return {
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "THE-LIMBO MVP Cockpit",
        "company": {
            "id": str(company_id),
            "name": company.name if company else "Unknown",
            "industry": company.industry if company else None,
            "cnpj_or_tax_id": company.cnpj_or_tax_id if company else None,
        },
        "summary": {
            "overall_health": dashboard.overall_health,
            "overall_health_label": HEALTH_LABELS.get(dashboard.overall_health, dashboard.overall_health),
            "total_at_risk": len(at_risk_items),
            "data_gaps_count": len(gaps),
        },
        "domains": domains,
        "at_risk_items": at_risk_items,
        "data_gaps": gaps,
        "recent_orchestrations": orchestrations,
        "external_import_template": _external_template(),
        "instructions": {
            "pt": (
                "Este relatório pode ser usado fora do ambiente Limbo. "
                "Exporte JSON para arquivar ou preencha external_import_template e reimporte via "
                "POST /api/v1/cockpit/report/import"
            ),
        },
    }


def build_portfolio_report(db: Session, company_ids: List[UUID]) -> dict:
    companies = [build_company_report(db, cid) for cid in company_ids]
    health_counts = {"green": 0, "yellow": 0, "red": 0}
    for c in companies:
        h = c["summary"]["overall_health"]
        if h in health_counts:
            health_counts[h] += 1

    return {
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "THE-LIMBO MVP Cockpit",
        "type": "portfolio",
        "company_count": len(companies),
        "portfolio_health": health_counts,
        "companies": companies,
        "instructions": {
            "pt": "Relatório consolidado de múltiplas startups. Cada bloco 'companies' é independente.",
        },
    }


def report_to_markdown(report: dict) -> str:
    if report.get("type") == "portfolio":
        return _portfolio_markdown(report)
    return _single_markdown(report)


def _single_markdown(report: dict) -> str:
    co = report["company"]
    s = report["summary"]
    lines = [
        f"# Relatório MVP — {co['name']}",
        "",
        f"**Gerado em:** {report['generated_at']}",
        f"**Saúde geral:** {s['overall_health_label']} ({s['overall_health']})",
        f"**KPIs em risco:** {s['total_at_risk']} | **Sem dados:** {s['data_gaps_count']}",
        "",
        f"**Empresa ID:** `{co['id']}`",
        f"**Indústria:** {co.get('industry') or '—'}",
        "",
        "---",
        "",
    ]

    for domain in report["domains"]:
        lines.append(f"## {domain['label']}")
        lines.append("")
        lines.append("| KPI | Atual | Meta | Gap | Status |")
        lines.append("|-----|-------|------|-----|--------|")
        for m in domain["metrics"]:
            cur = f"{m['current_value']:.1f}" if m["current_value"] is not None else "—"
            gap = f"{m['gap_percent']}%" if m["gap_percent"] is not None else "—"
            lines.append(
                f"| {m['label']} | {cur} {m['unit']} | {m['target_value']} {m['unit']} | {gap} | {m['status_label']} |"
            )
        lines.append("")

    if report["at_risk_items"]:
        lines.append("## Ações prioritárias (KPIs em risco)")
        lines.append("")
        for item in report["at_risk_items"]:
            lines.append(f"- **{item['domain']} / {item['metric']}**: atual {item['current']} vs meta {item['target']}")
        lines.append("")

    if report["data_gaps"]:
        lines.append("## Dados faltando (preencher manualmente se outro ambiente)")
        lines.append("")
        for gap in report["data_gaps"]:
            lines.append(f"- {gap}")
        lines.append("")

    if report.get("recent_orchestrations"):
        lines.append("## Últimas análises dos agentes")
        lines.append("")
        for o in report["recent_orchestrations"]:
            lines.append(f"### {o['objective'][:80]}")
            if o.get("synthesis"):
                lines.append(o["synthesis"][:1500])
            lines.append("")

    lines.append("---")
    lines.append("*Gerado por THE-LIMBO — portable report v" + REPORT_VERSION + "*")
    return "\n".join(lines)


def _portfolio_markdown(report: dict) -> str:
    lines = [
        f"# Relatório Portfolio — {report['company_count']} startups",
        "",
        f"**Gerado em:** {report['generated_at']}",
        f"**Saudáveis:** {report['portfolio_health'].get('green', 0)} | "
        f"**Atenção:** {report['portfolio_health'].get('yellow', 0)} | "
        f"**Críticas:** {report['portfolio_health'].get('red', 0)}",
        "",
        "---",
        "",
    ]
    for co_report in report["companies"]:
        lines.append(_single_markdown(co_report))
        lines.append("\n---\n")
    return "\n".join(lines)
