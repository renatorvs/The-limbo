"""Manager Agent — orchestrates multi-agent handoffs across domain workers."""

from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.core.models import Company
from app.modules.advisory import agent, schemas as advisory_schemas
from app.modules.agents import models, registry


DEFAULT_WORKERS = registry.DEFAULT_WORKERS

WORKER_PROMPTS = {
    "cfo": "Analise a situação financeira (runway, burn, saldo) relacionada a este objetivo:",
    "cmo": "Analise métricas de growth, campanhas e funil relacionadas a este objetivo:",
    "cpo": "Analise roadmap e métricas de engenharia relacionadas a este objetivo:",
    "cs": "Analise saúde dos clientes, NPS e tickets relacionados a este objetivo:",
}


async def run_orchestration(
    objective: str,
    company_id: Optional[str] = None,
    agents: Optional[List[str]] = None,
    db: Optional[Session] = None,
    user_id: Optional[str] = None,
) -> advisory_schemas.OrchestrationResponse:
    worker_ids = agents or DEFAULT_WORKERS
    steps: List[advisory_schemas.AgentStepResult] = []

    for agent_id in worker_ids:
        if agent_id not in registry.AGENT_REGISTRY:
            continue
        cfg = registry.get_agent(agent_id)
        sub_prompt = WORKER_PROMPTS.get(agent_id, "Analise este objetivo:")
        chat_req = advisory_schemas.ChatRequest(
            user_message=f"{sub_prompt}\n\nObjetivo: {objective}",
            company_id=company_id,
            agent_id=agent_id,
        )
        result = await agent.run_agent(chat_req)
        steps.append(
            advisory_schemas.AgentStepResult(
                agent_id=agent_id,
                label=cfg["label"],
                response=result.response,
                tools_used=result.tools_used,
            )
        )

    findings = "\n\n".join(f"### {s.label}\n{s.response}" for s in steps)
    synthesis_req = advisory_schemas.ChatRequest(
        user_message=(
            f"Sintetize as análises dos advisors abaixo em uma recomendação estratégica clara "
            f"com 3-5 ações prioritárias. Objetivo original: {objective}\n\n{findings}"
        ),
        company_id=company_id,
        agent_id="ceo",
    )
    synthesis_result = await agent.run_agent(synthesis_req)
    pending_actions = _extract_pending_actions(synthesis_result.response, company_id)

    if db is not None:
        _persist_run(db, objective, company_id, user_id, worker_ids, steps, synthesis_result.response, pending_actions)

    return advisory_schemas.OrchestrationResponse(
        objective=objective,
        company_id=company_id,
        steps=steps,
        synthesis=synthesis_result.response,
        pending_actions=pending_actions,
    )


async def run_multi_orchestration(
    objective: str,
    company_ids: List[str],
    agents: Optional[List[str]] = None,
    db: Optional[Session] = None,
    user_id: Optional[str] = None,
) -> advisory_schemas.MultiOrchestrationResponse:
    """Run orchestration in parallel for multiple startups, then portfolio synthesis."""
    company_results: List[advisory_schemas.CompanyOrchestrationResult] = []

    for cid in company_ids:
        result = await run_orchestration(
            objective=objective,
            company_id=cid,
            agents=agents,
            db=db,
            user_id=user_id,
        )
        name = None
        if db:
            co = db.query(Company).filter(Company.id == uuid.UUID(cid)).first()
            name = co.name if co else None
        company_results.append(
            advisory_schemas.CompanyOrchestrationResult(
                company_id=cid,
                company_name=name,
                steps=result.steps,
                synthesis=result.synthesis,
                pending_actions=result.pending_actions,
            )
        )

    portfolio_findings = "\n\n".join(
        f"### {r.company_name or r.company_id}\n{r.synthesis}" for r in company_results
    )
    portfolio_req = advisory_schemas.ChatRequest(
        user_message=(
            f"Você é o CEO de um portfolio com {len(company_ids)} startups. "
            f"Sintetize recomendações cross-portfolio, priorizando alocação de capital e foco. "
            f"Objetivo: {objective}\n\n{portfolio_findings}"
        ),
        agent_id="ceo",
    )
    portfolio_result = await agent.run_agent(portfolio_req)

    if db is not None:
        run = models.AgentOrchestrationRun(
            user_id=uuid.UUID(user_id) if user_id else None,
            objective=f"[PORTFOLIO] {objective}",
            agents_used=agents or DEFAULT_WORKERS,
            steps=[r.model_dump() for r in company_results],
            synthesis=portfolio_result.response,
        )
        db.add(run)
        db.commit()

    return advisory_schemas.MultiOrchestrationResponse(
        objective=objective,
        companies=company_results,
        portfolio_synthesis=portfolio_result.response,
    )


def _persist_run(db, objective, company_id, user_id, worker_ids, steps, synthesis, pending_actions):
    run = models.AgentOrchestrationRun(
        company_id=uuid.UUID(company_id) if company_id else None,
        user_id=uuid.UUID(user_id) if user_id else None,
        objective=objective,
        agents_used=worker_ids,
        steps=[s.model_dump() for s in steps],
        synthesis=synthesis,
    )
    db.add(run)
    for action in pending_actions:
        db.add(
            models.AgentAction(
                company_id=uuid.UUID(company_id) if company_id else None,
                user_id=uuid.UUID(user_id) if user_id else None,
                agent_id=action.get("agent_id", "ceo"),
                action_type=action.get("action_type", "recommendation"),
                description=action["description"],
                payload=action.get("payload", {}),
                status="pending",
            )
        )
    db.commit()


def _extract_pending_actions(synthesis: str, company_id: Optional[str]) -> List[dict]:
    triggers = ("investir", "contratar", "gastar", "budget", "aprovar", "lançar", "pivot")
    actions = []
    lower = synthesis.lower()
    if any(t in lower for t in triggers):
        actions.append({
            "agent_id": "ceo",
            "action_type": "strategic_decision",
            "description": "Recomendação estratégica requer aprovação humana (HI-C)",
            "payload": {"synthesis_excerpt": synthesis[:500], "company_id": company_id},
        })
    return actions
