"""Produtos conectados ao Limbo: INPUT → LIMBO → OUTPUT."""

PRODUCTS = {
    "sofia-education": {
        "name": "Sofia Education IA",
        "industry": "EdTech",
        "source_app": "sofia-education",
        "tagline": "IA educacional generativa para vestibulares e ENEM",
        "input_endpoint": "/api/v1/hub/sofia-education/input",
        "output_endpoint": "/api/v1/hub/sofia-education/output",
        "agent_reporter": "sofia-weekly-agent",
        "focus_domains": ["cfo", "cmo", "cpo", "cs"],
        "mvp_priorities": ["trial_conversion", "activation_rate", "nps_score", "runway_months"],
    },
    "bodyvision": {
        "name": "BodyVision.IA",
        "industry": "HealthTech",
        "source_app": "bodyvision",
        "tagline": "Análise corporal e fitness powered by IA",
        "input_endpoint": "/api/v1/hub/bodyvision/input",
        "output_endpoint": "/api/v1/hub/bodyvision/output",
        "agent_reporter": "bodyvision-weekly-agent",
        "focus_domains": ["cfo", "cmo", "cpo", "cs"],
        "mvp_priorities": ["dau", "trial_conversion", "cac", "churn_rate"],
    },
}


def get_product(app_key: str) -> dict | None:
    return PRODUCTS.get(app_key.lower())


def list_products() -> list[dict]:
    return [{"app_key": k, **v} for k, v in PRODUCTS.items()]
