from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import security
from app.core.models import User
from app.core.tenant import require_company_id
from app.modules.reports import schemas, service, report_format

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/ingest", response_model=schemas.ReportIngestResponse)
def ingest_report(
    body: schemas.AppReportIngest,
    db: Session = Depends(get_db),
):
    """
    **Fonte primária de dados** — apps externas enviam relatório JSON.
    Não requer acesso ao banco da app. Autenticação opcional via API key (futuro).
    """
    try:
        return service.ingest_report(db, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/format/sample")
def get_sample_format():
    """Retorna exemplo do JSON que os agentes das apps devem gerar."""
    return report_format.SAMPLE_REPORT


@router.get("/list", response_model=List[schemas.ReportSummaryOut])
def list_company_reports(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    reports = service.list_reports(db, company_id)
    return [
        schemas.ReportSummaryOut(
            id=r.id,
            source_app=r.source_app,
            generated_by_agent=r.generated_by_agent,
            period_end=r.period_end,
            executive_summary=(r.executive_summary or "")[:200],
            ingested_at=r.ingested_at,
            metrics_count=len(r.parsed_metrics or {}),
        )
        for r in reports
    ]


@router.get("/latest")
def get_latest_report(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(require_company_id),
):
    report = service.get_latest_report(db, company_id)
    if not report:
        return {"message": "Nenhum relatório ingerido. Use POST /ingest ou sync de banco (secundário)."}
    return {
        "id": str(report.id),
        "source_app": report.source_app,
        "generated_by_agent": report.generated_by_agent,
        "executive_summary": report.executive_summary,
        "metrics": report.parsed_metrics,
        "domain_narratives": report.domain_narratives,
        "ingested_at": report.ingested_at.isoformat(),
        "period": {"start": str(report.period_start), "end": str(report.period_end)},
    }


@router.get("/docs")
def reports_docs(request: Request):
    """Página com instruções para agentes das apps."""
    return templates.TemplateResponse("dashboard/reports_docs.html", {
        "request": request,
        "sample": report_format.SAMPLE_REPORT,
    })
