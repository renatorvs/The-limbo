"""LangChain tools that read live data from Limbo modules, scoped by company_id."""

import json
from typing import List, Optional
from uuid import UUID

from langchain_core.tools import StructuredTool
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.models import AnalyticsSaasMetricsDaily, Company
from app.modules.backbone import models as backbone_models
from app.modules.growth import models as growth_models
from app.modules.product import models as product_models
from app.modules.cs import models as cs_models


def _parse_company_id(company_id: str) -> Optional[UUID]:
    if not company_id:
        return None
    try:
        return UUID(str(company_id))
    except (ValueError, TypeError):
        return None


def _get_financial_stats(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        q_balance = db.query(func.sum(backbone_models.BankAccount.current_balance))
        q_burn = db.query(func.sum(backbone_models.Ledger.amount)).filter(
            backbone_models.Ledger.type == "opex"
        )
        q_headcount = db.query(func.count(backbone_models.Staff.id)).filter(
            backbone_models.Staff.terminated_at.is_(None)
        )
        if cid:
            q_balance = q_balance.filter(backbone_models.BankAccount.company_id == cid)
            q_burn = q_burn.filter(backbone_models.Ledger.company_id == cid)
            q_headcount = q_headcount.filter(backbone_models.Staff.company_id == cid)

        total_balance = float(q_balance.scalar() or 0)
        burn_rate = float(q_burn.scalar() or 0)
        headcount = int(q_headcount.scalar() or 0)
        months_left = round(total_balance / burn_rate, 1) if burn_rate > 0 else None

        return json.dumps({
            "total_balance": total_balance,
            "monthly_burn_rate": burn_rate,
            "headcount": headcount,
            "runway_months": months_left,
        }, ensure_ascii=False)
    finally:
        db.close()


def _get_runway(company_id: str) -> str:
    stats = json.loads(_get_financial_stats(company_id))
    return json.dumps({
        "months_left": stats.get("runway_months"),
        "burn_rate": stats.get("monthly_burn_rate"),
        "cash_balance": stats.get("total_balance"),
    }, ensure_ascii=False)


def _get_growth_metrics(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        q = db.query(AnalyticsSaasMetricsDaily)
        if cid:
            q = q.filter(AnalyticsSaasMetricsDaily.company_id == cid)
        latest = q.order_by(desc(AnalyticsSaasMetricsDaily.reference_date)).first()

        if latest:
            return json.dumps({
                "arr": float(latest.arr or 0),
                "mrr": float(latest.mrr or 0),
                "cac": float(latest.cac or 0),
                "ltv": float(latest.ltv or 0),
                "churn_rate_percent": float(latest.churn_rate_percent or 0),
                "nps_score": int(latest.nps_score or 0),
                "reference_date": str(latest.reference_date),
            }, ensure_ascii=False)

        return json.dumps({"message": "No growth metrics found for this company."}, ensure_ascii=False)
    finally:
        db.close()


def _get_active_campaigns(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        q = db.query(growth_models.Campaign).filter(growth_models.Campaign.status == "Active")
        if cid:
            q = q.filter(growth_models.Campaign.company_id == cid)
        campaigns = q.limit(10).all()
        return json.dumps([
            {
                "name": c.name,
                "channel": c.channel,
                "budget_total": float(c.budget_total or 0),
                "status": c.status,
            }
            for c in campaigns
        ], ensure_ascii=False)
    finally:
        db.close()


def _get_funnel_snapshot(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        q = db.query(growth_models.FunnelSnapshot)
        if cid:
            q = q.filter(growth_models.FunnelSnapshot.company_id == cid)
        snapshot = q.order_by(desc(growth_models.FunnelSnapshot.date)).first()
        if not snapshot:
            return json.dumps({"message": "No funnel data found."}, ensure_ascii=False)
        return json.dumps({
            "date": str(snapshot.date),
            "visitors": snapshot.visitors,
            "leads": snapshot.leads,
            "mql": snapshot.mql,
            "sql": snapshot.sql,
            "customers": snapshot.customers,
            "cac": float(snapshot.cac or 0),
        }, ensure_ascii=False)
    finally:
        db.close()


def _get_roadmap(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        q = db.query(product_models.RoadmapItem)
        if cid:
            q = q.filter(product_models.RoadmapItem.company_id == cid)
        items = q.order_by(product_models.RoadmapItem.created_at.desc()).limit(15).all()
        return json.dumps([
            {
                "title": i.title,
                "status": i.status,
                "priority": i.priority,
                "target_date": str(i.target_date) if i.target_date else None,
            }
            for i in items
        ], ensure_ascii=False)
    finally:
        db.close()


def _get_engineering_metrics(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        metrics = {}
        for name in ("uptime", "bugs_open", "deploy_frequency"):
            q = db.query(product_models.EngineeringMetrics).filter(
                product_models.EngineeringMetrics.metric_name == name
            )
            if cid:
                q = q.filter(product_models.EngineeringMetrics.company_id == cid)
            row = q.order_by(desc(product_models.EngineeringMetrics.measured_at)).first()
            metrics[name] = float(row.value) if row else None
        return json.dumps(metrics, ensure_ascii=False)
    finally:
        db.close()


def _get_cs_dashboard(company_id: str) -> str:
    cid = _parse_company_id(company_id)
    db: Session = SessionLocal()
    try:
        cust_q = db.query(
            func.sum(cs_models.Customer.mrr_value).label("total_mrr"),
            func.count(cs_models.Customer.id).label("active_customers"),
        ).filter(cs_models.Customer.churned_at.is_(None))
        if cid:
            cust_q = cust_q.filter(cs_models.Customer.company_id == cid)
        financials = cust_q.first()

        nps_q = db.query(cs_models.NpsSurvey)
        if cid:
            nps_q = nps_q.filter(cs_models.NpsSurvey.company_id == cid)
        surveys = nps_q.all()

        promoters = sum(1 for s in surveys if s.score >= 9)
        detractors = sum(1 for s in surveys if s.score <= 6)
        total = len(surveys)
        nps = round(((promoters - detractors) / total) * 100) if total else 0

        ticket_q = db.query(func.count(cs_models.Ticket.id)).filter(
            cs_models.Ticket.status.in_(["open", "pending"])
        )
        open_tickets = int(ticket_q.scalar() or 0)

        return json.dumps({
            "total_mrr": float(financials.total_mrr or 0),
            "active_customers": int(financials.active_customers or 0),
            "nps_score": nps,
            "open_tickets": open_tickets,
        }, ensure_ascii=False)
    finally:
        db.close()


def _list_companies() -> str:
    db: Session = SessionLocal()
    try:
        companies = db.query(Company).all()
        return json.dumps([
            {"id": str(c.id), "name": c.name, "industry": c.industry}
            for c in companies
        ], ensure_ascii=False)
    finally:
        db.close()


# Tool groups per agent persona
CFO_TOOLS = ("get_financial_stats", "get_runway", "propose_write_action")
CMO_TOOLS = ("get_growth_metrics", "get_active_campaigns", "get_funnel_snapshot", "propose_write_action")
CPO_TOOLS = ("get_roadmap", "get_engineering_metrics", "propose_write_action")
CS_TOOLS = ("get_cs_dashboard", "propose_write_action")
CEO_TOOLS = ("get_financial_stats", "get_growth_metrics", "get_roadmap", "get_cs_dashboard", "list_companies", "propose_write_action")
MANAGER_TOOLS = CEO_TOOLS


def _propose_write_action(
    company_id: str,
    agent_id: str,
    action_type: str,
    description: str,
    payload_json: str = "{}",
) -> str:
    """Queue a write action for human approval (HI-C)."""
    from app.modules.agents.models import AgentAction

    db: Session = SessionLocal()
    try:
        payload = json.loads(payload_json) if payload_json else {}
        cid = _parse_company_id(company_id)
        action = AgentAction(
            company_id=cid,
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            payload=payload,
            status="pending",
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return json.dumps({
            "status": "pending_approval",
            "action_id": str(action.id),
            "message": "Ação enviada para aprovação humana no Command Center (HI-C).",
        }, ensure_ascii=False)
    except Exception as e:
        db.rollback()
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
    finally:
        db.close()


def build_tools(company_id: str, agent_id: str = "cfo") -> List[StructuredTool]:
    """Build LangChain tools scoped to a company and agent persona."""
    cid = company_id or ""

    all_tools = {
        "get_financial_stats": StructuredTool.from_function(
            func=lambda: _get_financial_stats(cid),
            name="get_financial_stats",
            description="Get total balance, monthly burn rate, headcount, and runway for the company.",
        ),
        "get_runway": StructuredTool.from_function(
            func=lambda: _get_runway(cid),
            name="get_runway",
            description="Get cash runway in months and current burn rate.",
        ),
        "get_growth_metrics": StructuredTool.from_function(
            func=lambda: _get_growth_metrics(cid),
            name="get_growth_metrics",
            description="Get latest SaaS metrics: ARR, MRR, CAC, LTV, churn, NPS.",
        ),
        "get_active_campaigns": StructuredTool.from_function(
            func=lambda: _get_active_campaigns(cid),
            name="get_active_campaigns",
            description="List active marketing campaigns with channel and budget.",
        ),
        "get_funnel_snapshot": StructuredTool.from_function(
            func=lambda: _get_funnel_snapshot(cid),
            name="get_funnel_snapshot",
            description="Get latest marketing funnel snapshot (visitors → customers).",
        ),
        "get_roadmap": StructuredTool.from_function(
            func=lambda: _get_roadmap(cid),
            name="get_roadmap",
            description="Get product roadmap items with status and priority.",
        ),
        "get_engineering_metrics": StructuredTool.from_function(
            func=lambda: _get_engineering_metrics(cid),
            name="get_engineering_metrics",
            description="Get engineering metrics: uptime, open bugs, deploy frequency.",
        ),
        "get_cs_dashboard": StructuredTool.from_function(
            func=lambda: _get_cs_dashboard(cid),
            name="get_cs_dashboard",
            description="Get CS metrics: MRR, active customers, NPS, open tickets.",
        ),
        "list_companies": StructuredTool.from_function(
            func=_list_companies,
            name="list_companies",
            description="List all startups/companies managed in the platform.",
        ),
        "propose_write_action": StructuredTool.from_function(
            func=lambda action_type, description, payload_json="{}": _propose_write_action(
                cid, agent_id.lower(), action_type, description, payload_json
            ),
            name="propose_write_action",
            description=(
                "Propose a write action requiring human approval (HI-C). "
                "action_type: create_campaign, create_roadmap, move_roadmap, create_transaction, create_customer. "
                "payload_json: JSON string with action fields (name, budget_total, title, amount, etc)."
            ),
        ),
    }

    tool_map = {
        "cfo": CFO_TOOLS,
        "cmo": CMO_TOOLS,
        "cpo": CPO_TOOLS,
        "cs": CS_TOOLS,
        "ceo": CEO_TOOLS,
        "manager": MANAGER_TOOLS,
    }
    selected = tool_map.get(agent_id.lower(), CFO_TOOLS)
    return [all_tools[name] for name in selected if name in all_tools]
