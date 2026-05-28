"""Ingestão e leitura de relatórios de apps externas."""

from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import Company
from app.modules.reports import models, schemas, parser
from app.modules.advisory import models as advisory_models
from app.modules.agents import models as agent_models


def ingest_report(db: Session, report: schemas.AppReportIngest, queue_actions: bool = True) -> schemas.ReportIngestResponse:
    company_id = parser.resolve_company_id(db, report.company_ref)
    if not company_id:
        raise ValueError(
            f"Empresa não encontrada. Cadastre no Limbo e passe company_ref.id "
            f"(recebido: id={report.company_ref.id}, key={report.company_ref.key}, name={report.company_ref.name})"
        )

    # Marca relatórios anteriores como superseded
    db.query(models.CompanyReport).filter(
        models.CompanyReport.company_id == company_id,
        models.CompanyReport.source_app == report.source_app,
        models.CompanyReport.status == "active",
    ).update({"status": "superseded"})

    parsed_metrics = parser.extract_metrics(report.domains)
    narratives = parser.build_domain_narratives(report.domains)

    db_report = models.CompanyReport(
        company_id=company_id,
        source_app=report.source_app,
        generated_by_agent=report.generated_by_agent,
        report_version=report.limbo_report_version,
        period_start=report.period.start if report.period else None,
        period_end=report.period.end if report.period else None,
        executive_summary=report.executive_summary,
        raw_payload=report.model_dump(mode="json"),
        parsed_metrics=parsed_metrics,
        domain_narratives=narratives,
        generated_at=report.generated_at,
        status="active",
    )
    db.add(db_report)
    db.flush()

    # Indexa no RAG (advisory knowledge base)
    rag_text = parser.build_rag_content(report)
    kb = advisory_models.AdvisoryKnowledgeBase(
        company_id=company_id,
        content=rag_text,
        source_title=f"Relatório {report.source_app} — {report.period.end if report.period else 'atual'}",
        source_type="agent_report",
    )
    db.add(kb)

    actions_queued = 0
    if queue_actions and report.actions_proposed:
        for action in report.actions_proposed:
            db.add(agent_models.AgentAction(
                company_id=company_id,
                agent_id=action.agent_id,
                action_type=action.action_type,
                description=f"[{report.source_app}] {action.description}",
                payload={**action.payload, "source_report_id": str(db_report.id)},
                status="pending",
            ))
            actions_queued += 1

    db.commit()
    db.refresh(db_report)

    return schemas.ReportIngestResponse(
        report_id=db_report.id,
        company_id=str(company_id),
        metrics_extracted=len(parsed_metrics),
        knowledge_indexed=True,
        actions_queued=actions_queued,
        message=f"Relatório de '{report.source_app}' ingerido. {len(parsed_metrics)} KPIs extraídos.",
    )


def get_latest_metrics(db: Session, company_id: UUID, max_age_hours: int = 168) -> Optional[Dict[str, float]]:
    """Retorna KPIs do relatório mais recente (fonte primária)."""
    report = (
        db.query(models.CompanyReport)
        .filter(
            models.CompanyReport.company_id == company_id,
            models.CompanyReport.status == "active",
        )
        .order_by(desc(models.CompanyReport.ingested_at))
        .first()
    )
    if not report or not report.parsed_metrics:
        return None
    return {k: float(v) for k, v in report.parsed_metrics.items()}


def get_latest_report(db: Session, company_id: UUID) -> Optional[models.CompanyReport]:
    return (
        db.query(models.CompanyReport)
        .filter(
            models.CompanyReport.company_id == company_id,
            models.CompanyReport.status == "active",
        )
        .order_by(desc(models.CompanyReport.ingested_at))
        .first()
    )


def list_reports(db: Session, company_id: UUID, limit: int = 20) -> List[models.CompanyReport]:
    return (
        db.query(models.CompanyReport)
        .filter(models.CompanyReport.company_id == company_id)
        .order_by(desc(models.CompanyReport.ingested_at))
        .limit(limit)
        .all()
    )
