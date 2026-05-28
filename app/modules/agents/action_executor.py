"""Execute approved HI-C write actions against domain modules."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.agents import models
from app.modules.growth import service as growth_service, schemas as growth_schemas
from app.modules.product import service as product_service, schemas as product_schemas
from app.modules.backbone import service as backbone_service, schemas as backbone_schemas
from app.modules.cs import service as cs_service, schemas as cs_schemas


SUPPORTED_ACTIONS = {
    "create_campaign",
    "create_roadmap",
    "move_roadmap",
    "create_transaction",
    "create_customer",
    "strategic_decision",
}


def execute_action(db: Session, action: models.AgentAction) -> dict:
    """Execute an approved AgentAction. Returns result dict."""
    action_type = action.action_type
    payload = action.payload or {}
    company_id = action.company_id or payload.get("company_id")

    if action_type == "create_campaign":
        return _create_campaign(db, payload, company_id)
    if action_type == "create_roadmap":
        return _create_roadmap(db, payload, company_id)
    if action_type == "move_roadmap":
        return _move_roadmap(db, payload, company_id)
    if action_type == "create_transaction":
        return _create_transaction(db, payload, company_id)
    if action_type == "create_customer":
        return _create_customer(db, payload, company_id)
    if action_type == "strategic_decision":
        return {"status": "acknowledged", "message": "Decisão estratégica aprovada pelo humano."}

    return {"status": "skipped", "message": f"Action type '{action_type}' not executable yet."}


def _uuid(val) -> Optional[uuid.UUID]:
    if not val:
        return None
    return uuid.UUID(str(val))


def _create_campaign(db: Session, payload: dict, company_id) -> dict:
    campaign = growth_schemas.CampaignCreate(
        name=payload.get("name", "Nova Campanha"),
        channel=payload.get("channel", "digital"),
        status=payload.get("status", "Active"),
        budget_total=float(payload.get("budget_total", 0)),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
        company_id=_uuid(company_id),
    )
    result = growth_service.create_campaign(db, campaign)
    return {"status": "created", "id": str(result.id), "name": result.name}


def _create_roadmap(db: Session, payload: dict, company_id) -> dict:
    item = product_schemas.RoadmapItemCreate(
        title=payload.get("title", "Novo Item"),
        description=payload.get("description"),
        status=payload.get("status", "backlog"),
        priority=payload.get("priority", "medium"),
        strategic_goal=payload.get("strategic_goal"),
        target_date=payload.get("target_date"),
        company_id=_uuid(company_id),
    )
    result = product_service.create_roadmap_item(db, item)
    return {"status": "created", "id": str(result.id), "title": result.title}


def _move_roadmap(db: Session, payload: dict, company_id) -> dict:
    from app.modules.product import models as product_models

    item_id = _uuid(payload.get("item_id"))
    new_status = payload.get("status", "in_progress")
    item = db.query(product_models.RoadmapItem).filter(
        product_models.RoadmapItem.id == item_id
    ).first()
    if not item:
        return {"status": "error", "message": "Roadmap item not found"}
    if company_id and str(item.company_id) != str(company_id):
        return {"status": "error", "message": "Item belongs to another company"}
    item.status = new_status
    db.commit()
    return {"status": "updated", "id": str(item.id), "new_status": new_status}


def _create_transaction(db: Session, payload: dict, company_id) -> dict:
    txn = backbone_schemas.LedgerCreate(
        description=payload.get("description", "Agent-initiated transaction"),
        amount=float(payload.get("amount", 0)),
        type=payload.get("type", "opex"),
        transaction_date=payload.get("transaction_date") or date.today(),
        company_id=_uuid(company_id),
        cost_center_id=_uuid(payload.get("cost_center_id")),
        account_id=_uuid(payload.get("account_id")),
        status=payload.get("status", "pending"),
    )
    result = backbone_service.create_transaction(db, txn)
    return {"status": "created", "id": str(result.id), "amount": float(result.amount)}


def _create_customer(db: Session, payload: dict, company_id) -> dict:
    customer = cs_schemas.CustomerCreate(
        name=payload.get("name", "Novo Cliente"),
        plan_name=payload.get("plan_name", "basic"),
        mrr_value=float(payload.get("mrr_value", 0)),
        health_score=int(payload.get("health_score", 80)),
        onboarding_status=payload.get("onboarding_status", "active"),
        churned_at=None,
        external_source_id=payload.get("external_source_id"),
        last_xp_score=payload.get("last_xp_score"),
        company_id=_uuid(company_id),
    )
    result = cs_service.create_customer(db, customer)
    return {"status": "created", "id": str(result.id), "name": result.name}
