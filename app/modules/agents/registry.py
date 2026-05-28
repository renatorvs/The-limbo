"""Agent registry — maps agent IDs to personas, tools, and labels."""

from app.modules.advisory import prompts, tools

DEFAULT_WORKERS = ["cfo", "cmo", "cpo", "cs"]

AGENT_REGISTRY = {
    "cfo": {"id": "cfo", "label": prompts.PERSONA_LABELS["cfo"], "persona": prompts.CFO_PERSONA, "tool_names": tools.CFO_TOOLS},
    "cmo": {"id": "cmo", "label": prompts.PERSONA_LABELS["cmo"], "persona": prompts.CMO_PERSONA, "tool_names": tools.CMO_TOOLS},
    "cpo": {"id": "cpo", "label": prompts.PERSONA_LABELS["cpo"], "persona": prompts.CPO_PERSONA, "tool_names": tools.CPO_TOOLS},
    "cs": {"id": "cs", "label": prompts.PERSONA_LABELS["cs"], "persona": prompts.CS_PERSONA, "tool_names": tools.CS_TOOLS},
    "ceo": {"id": "ceo", "label": prompts.PERSONA_LABELS["ceo"], "persona": prompts.CEO_PERSONA, "tool_names": tools.CEO_TOOLS},
    "manager": {"id": "manager", "label": prompts.PERSONA_LABELS["manager"], "persona": prompts.MANAGER_PERSONA, "tool_names": tools.MANAGER_TOOLS},
}


def list_agents() -> list[dict]:
    return [
        {"id": cfg["id"], "label": cfg["label"], "tool_names": list(cfg["tool_names"])}
        for cfg in AGENT_REGISTRY.values()
    ]


def get_agent(agent_id: str) -> dict:
    return AGENT_REGISTRY.get(agent_id.lower(), AGENT_REGISTRY["cfo"])
