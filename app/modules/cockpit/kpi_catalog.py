"""Catálogo de KPIs essenciais para MVP por área de atuação."""

MVP_KPI_CATALOG = {
    "cfo": [
        {"key": "runway_months", "label": "Runway", "unit": "meses", "default_target": 12, "critical_below": 6, "direction": "above"},
        {"key": "monthly_burn", "label": "Burn Rate", "unit": "R$/mês", "default_target": 50000, "critical_below": None, "direction": "below"},
        {"key": "total_balance", "label": "Caixa", "unit": "R$", "default_target": 600000, "critical_below": 100000, "direction": "above"},
        {"key": "mrr", "label": "MRR", "unit": "R$", "default_target": 10000, "critical_below": 3000, "direction": "above"},
    ],
    "cmo": [
        {"key": "cac", "label": "CAC", "unit": "R$", "default_target": 150, "critical_below": None, "direction": "below"},
        {"key": "ltv_cac_ratio", "label": "LTV:CAC", "unit": "x", "default_target": 3, "critical_below": 1, "direction": "above"},
        {"key": "trial_conversion", "label": "Conversão Trial", "unit": "%", "default_target": 15, "critical_below": 5, "direction": "above"},
        {"key": "leads", "label": "Leads/mês", "unit": "#", "default_target": 200, "critical_below": 50, "direction": "above"},
    ],
    "cpo": [
        {"key": "dau", "label": "DAU", "unit": "#", "default_target": 100, "critical_below": 20, "direction": "above"},
        {"key": "activation_rate", "label": "Ativação", "unit": "%", "default_target": 40, "critical_below": 15, "direction": "above"},
        {"key": "bugs_open", "label": "Bugs Abertos", "unit": "#", "default_target": 5, "critical_below": None, "direction": "below"},
        {"key": "uptime", "label": "Uptime", "unit": "%", "default_target": 99.5, "critical_below": 98, "direction": "above"},
    ],
    "cs": [
        {"key": "nps_score", "label": "NPS", "unit": "pts", "default_target": 50, "critical_below": 20, "direction": "above"},
        {"key": "churn_rate", "label": "Churn", "unit": "%", "default_target": 3, "critical_below": None, "direction": "below"},
        {"key": "active_customers", "label": "Clientes Ativos", "unit": "#", "default_target": 50, "critical_below": 10, "direction": "above"},
        {"key": "open_tickets", "label": "Tickets Abertos", "unit": "#", "default_target": 5, "critical_below": None, "direction": "below"},
    ],
}

DOMAIN_LABELS = {
    "cfo": "Finanças",
    "cmo": "Growth",
    "cpo": "Produto",
    "cs": "Customer Success",
}
