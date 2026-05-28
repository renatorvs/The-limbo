"""Parse relatórios de apps externas em KPIs e narrativas."""

from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import Company
from app.modules.reports.report_format import METRIC_ALIASES
from app.modules.reports import schemas


def resolve_company_id(db: Session, ref: schemas.CompanyRef) -> Optional[UUID]:
    if ref.id:
        try:
            return UUID(ref.id)
        except ValueError:
            pass
    if ref.key:
        co = db.query(Company).filter(Company.app_key == ref.key).first()
        if not co:
            co = db.query(Company).filter(Company.name.ilike(f"%{ref.key}%")).first()
        if co:
            return co.id
    if ref.name:
        co = db.query(Company).filter(Company.name.ilike(ref.name)).first()
        if co:
            return co.id
    return None


def extract_metrics(domains: Dict[str, schemas.DomainReport]) -> Dict[str, float]:
    """Flatten domain metrics into cockpit metric_keys."""
    raw: Dict[str, float] = {}
    for domain_data in domains.values():
        for key, val in domain_data.metrics.items():
            raw[key] = float(val)

    flat: Dict[str, float] = {}
    for canonical, aliases in METRIC_ALIASES.items():
        for alias in aliases:
            if alias in raw:
                flat[canonical] = raw[alias]
                break
    return flat


def build_domain_narratives(domains: Dict[str, schemas.DomainReport]) -> dict:
    return {
        domain: {
            "highlights": d.highlights,
            "risks": d.risks,
            "recommendations": d.recommendations,
        }
        for domain, d in domains.items()
    }


def build_rag_content(report: schemas.AppReportIngest) -> str:
    """Texto para indexar na base de conhecimento do advisory."""
    parts = [f"# Relatório {report.source_app}"]
    if report.executive_summary:
        parts.append(f"## Resumo\n{report.executive_summary}")
    for domain, data in report.domains.items():
        parts.append(f"\n## {domain.upper()}")
        if data.metrics:
            metrics_str = ", ".join(f"{k}={v}" for k, v in data.metrics.items())
            parts.append(f"Métricas: {metrics_str}")
        for h in data.highlights:
            parts.append(f"- OK: {h}")
        for r in data.risks:
            parts.append(f"- RISCO: {r}")
        for rec in data.recommendations:
            parts.append(f"- AÇÃO: {rec}")
    return "\n".join(parts)
