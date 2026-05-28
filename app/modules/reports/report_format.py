"""Formato padrão de relatório que apps externas enviam ao Limbo.

Os agentes de cada app (Sofia, Startup B, etc.) geram este JSON periodicamente.
O Limbo NÃO precisa acessar o banco da app — só lê e entende o relatório.

Versão: 1.0
"""

LIMBO_REPORT_VERSION = "1.0"

# Mapeamento metric_key do cockpit → chave no JSON do relatório
METRIC_ALIASES = {
    "runway_months": ["runway_months", "runway"],
    "monthly_burn": ["monthly_burn", "burn_rate", "burn"],
    "total_balance": ["total_balance", "cash", "caixa"],
    "mrr": ["mrr"],
    "cac": ["cac"],
    "ltv_cac_ratio": ["ltv_cac_ratio", "ltv_cac"],
    "trial_conversion": ["trial_conversion", "trial_conversion_rate"],
    "leads": ["leads"],
    "dau": ["dau"],
    "activation_rate": ["activation_rate"],
    "bugs_open": ["bugs_open", "open_bugs"],
    "uptime": ["uptime"],
    "nps_score": ["nps_score", "nps"],
    "churn_rate": ["churn_rate", "churn"],
    "active_customers": ["active_customers", "customers"],
    "open_tickets": ["open_tickets", "tickets_open"],
}

SAMPLE_REPORT = {
    "limbo_report_version": "1.0",
    "company_ref": {
        "id": "UUID-DA-EMPRESA-NO-LIMBO",
        "name": "Sofia EdTech",
        "key": "sofia",
    },
    "source_app": "sofia",
    "generated_at": "2026-05-24T10:00:00Z",
    "generated_by_agent": "sofia-weekly-agent",
    "period": {"start": "2026-05-17", "end": "2026-05-24"},
    "executive_summary": (
        "Semana positiva: MRR +8%, NPS estável. Runway 14 meses. "
        "Risco: churn subiu em plano básico. Recomendo campanha de retenção."
    ),
    "domains": {
        "cfo": {
            "metrics": {
                "runway_months": 14,
                "monthly_burn": 45000,
                "total_balance": 630000,
                "mrr": 12000,
            },
            "highlights": ["Runway acima da meta de 12 meses"],
            "risks": ["Burn subiu 8% vs mês anterior"],
            "recommendations": ["Renegociar contrato de cloud"],
        },
        "cmo": {
            "metrics": {"cac": 120, "ltv_cac_ratio": 3.5, "leads": 180, "trial_conversion": 18},
            "highlights": ["CAC abaixo da meta"],
            "risks": ["Conversão trial estagnada"],
            "recommendations": ["Testar onboarding email D1-D3"],
        },
        "cpo": {
            "metrics": {"dau": 850, "activation_rate": 42, "bugs_open": 7, "uptime": 99.7},
            "highlights": ["Ativação acima de 40%"],
            "risks": ["7 bugs abertos em produção"],
            "recommendations": ["Sprint de estabilização"],
        },
        "cs": {
            "metrics": {"nps_score": 55, "churn_rate": 2.8, "active_customers": 320, "open_tickets": 4},
            "highlights": ["NPS acima de 50"],
            "risks": ["3 clientes com health score < 40"],
            "recommendations": ["Outreach proativo nos 3 accounts"],
        },
    },
    "actions_proposed": [
        {
            "agent_id": "cmo",
            "action_type": "create_campaign",
            "description": "Campanha retenção plano básico",
            "payload": {"name": "Retenção Maio", "channel": "email", "budget_total": 2000},
        }
    ],
}
