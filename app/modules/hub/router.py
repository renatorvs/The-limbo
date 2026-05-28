from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.hub import service, schemas, products
from app.modules.reports import schemas as report_schemas
from app.modules.reports import report_format

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def hub_dashboard(request: Request, db: Session = Depends(get_db)):
    """Central INPUT → LIMBO → OUTPUT para Sofia e BodyVision."""
    statuses = service.get_products_status(db)
    return templates.TemplateResponse("dashboard/hub.html", {
        "request": request,
        "products": products.list_products(),
        "statuses": statuses,
    })


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    service.ensure_products(db)
    return products.list_products()


@router.get("/status")
def products_status(db: Session = Depends(get_db)):
    return service.get_products_status(db)


# ─── SOFIA EDUCATION IA ───────────────────────────────────────────

@router.post("/sofia-education/input", response_model=schemas.HubInputResponse)
def sofia_input(body: report_schemas.AppReportIngest, db: Session = Depends(get_db)):
    """INPUT ← Sofia Education IA (relatório do agente da app)."""
    try:
        return service.process_input(db, "sofia-education", body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sofia-education/output", response_model=schemas.HubOutput)
def sofia_output(db: Session = Depends(get_db)):
    """OUTPUT → Sofia Education IA (briefing, alertas, ações aprovadas)."""
    out = service.get_output(db, "sofia-education")
    if not out:
        raise HTTPException(status_code=404, detail="Sofia não configurada")
    return out


@router.post("/sofia-education/output/ack")
def sofia_output_ack(db: Session = Depends(get_db)):
    service.get_output(db, "sofia-education", mark_consumed=True)
    return {"acknowledged": True}


# ─── BODYVISION.IA ──────────────────────────────────────────────────

@router.post("/bodyvision/input", response_model=schemas.HubInputResponse)
def bodyvision_input(body: report_schemas.AppReportIngest, db: Session = Depends(get_db)):
    """INPUT ← BodyVision.IA (relatório do agente da app)."""
    try:
        return service.process_input(db, "bodyvision", body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bodyvision/output", response_model=schemas.HubOutput)
def bodyvision_output(db: Session = Depends(get_db)):
    """OUTPUT → BodyVision.IA (briefing, alertas, ações aprovadas)."""
    out = service.get_output(db, "bodyvision")
    if not out:
        raise HTTPException(status_code=404, detail="BodyVision não configurada")
    return out


@router.post("/bodyvision/output/ack")
def bodyvision_output_ack(db: Session = Depends(get_db)):
    service.get_output(db, "bodyvision", mark_consumed=True)
    return {"acknowledged": True}


@router.get("/samples/{app_key}")
def get_sample_input(app_key: str):
    """Exemplo de INPUT para cada produto."""
    samples = {
        "sofia-education": _sofia_sample(),
        "bodyvision": _bodyvision_sample(),
    }
    if app_key not in samples:
        raise HTTPException(status_code=404, detail="app_key inválido")
    return samples[app_key]


def _sofia_sample():
    s = dict(report_format.SAMPLE_REPORT)
    s["company_ref"] = {"key": "sofia-education", "name": "Sofia Education IA"}
    s["source_app"] = "sofia-education"
    s["generated_by_agent"] = "sofia-weekly-agent"
    s["executive_summary"] = (
        "Sofia: +12% trials, NPS 58. Runway 14 meses. "
        "Foco: melhorar ativação pós-cadastro e reter plano básico."
    )
    return s


def _bodyvision_sample():
    return {
        "limbo_report_version": "1.0",
        "company_ref": {"key": "bodyvision", "name": "BodyVision.IA"},
        "source_app": "bodyvision",
        "generated_by_agent": "bodyvision-weekly-agent",
        "period": {"start": "2026-05-17", "end": "2026-05-24"},
        "executive_summary": (
            "BodyVision: DAU +22%, 890 scans/semana. CAC R$95. "
            "Risco: churn 4.2% no plano free-to-paid. Priorizar onboarding do relatório PDF."
        ),
        "domains": {
            "cfo": {
                "metrics": {"runway_months": 18, "monthly_burn": 32000, "mrr": 8500},
                "highlights": ["Runway confortável"],
                "risks": [],
                "recommendations": ["Manter burn controlado"],
            },
            "cmo": {
                "metrics": {"cac": 95, "ltv_cac_ratio": 4.1, "leads": 420, "trial_conversion": 22},
                "highlights": ["CAC abaixo de R$120"],
                "risks": ["Conversão free→paid estagnada"],
                "recommendations": ["Testar trial de 14 dias com PDF premium"],
            },
            "cpo": {
                "metrics": {"dau": 890, "activation_rate": 55, "bugs_open": 3, "uptime": 99.9},
                "highlights": ["DAU crescendo", "Uptime excelente"],
                "risks": [],
                "recommendations": ["Feature: comparativo semanal de scans"],
            },
            "cs": {
                "metrics": {"nps_score": 62, "churn_rate": 4.2, "active_customers": 180, "open_tickets": 2},
                "highlights": ["NPS forte"],
                "risks": ["Churn acima da meta 3%"],
                "recommendations": ["Email D7 com dicas personalizadas"],
            },
        },
        "actions_proposed": [],
    }
