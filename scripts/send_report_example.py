#!/usr/bin/env python3
"""
Exemplo: agente da Sofia (ou qualquer app) envia relatório ao Limbo.

Não precisa estar no mesmo banco/ambiente — só HTTP POST com JSON.

Uso:
  python scripts/send_report_example.py --limbo-url http://localhost:8000 --company-id UUID
"""

import argparse
import json
import urllib.request
from datetime import date, timedelta

SAMPLE = {
    "limbo_report_version": "1.0",
    "company_ref": {"id": None, "name": "Sofia EdTech", "key": "sofia"},
    "source_app": "sofia",
    "generated_by_agent": "sofia-weekly-reporter",
    "period": {
        "start": str(date.today() - timedelta(days=7)),
        "end": str(date.today()),
    },
    "executive_summary": (
        "Semana positiva: MRR +8%, 42 novos trials. Runway 14 meses. "
        "Risco: 3 clientes com health score baixo no plano básico."
    ),
    "domains": {
        "cfo": {
            "metrics": {"runway_months": 14, "monthly_burn": 45000, "total_balance": 630000, "mrr": 12000},
            "highlights": ["Runway acima da meta"],
            "risks": ["Burn +8% vs mês anterior"],
            "recommendations": ["Renegociar cloud"],
        },
        "cmo": {
            "metrics": {"cac": 120, "ltv_cac_ratio": 3.5, "leads": 180, "trial_conversion": 18},
            "highlights": ["CAC abaixo da meta R$150"],
            "risks": ["Conversão trial estagnada"],
            "recommendations": ["A/B test landing page"],
        },
        "cpo": {
            "metrics": {"dau": 850, "activation_rate": 42, "bugs_open": 7, "uptime": 99.7},
            "highlights": ["Ativação > 40%"],
            "risks": ["7 bugs em prod"],
            "recommendations": ["Sprint estabilização"],
        },
        "cs": {
            "metrics": {"nps_score": 55, "churn_rate": 2.8, "active_customers": 320, "open_tickets": 4},
            "highlights": ["NPS > 50"],
            "risks": ["3 accounts em risco"],
            "recommendations": ["Outreach proativo"],
        },
    },
    "actions_proposed": [],
}


def main():
    parser = argparse.ArgumentParser(description="Envia relatório de exemplo ao Limbo")
    parser.add_argument("--limbo-url", default="http://localhost:8000")
    parser.add_argument("--company-id", required=True, help="UUID da empresa no Limbo")
    args = parser.parse_args()

    payload = dict(SAMPLE)
    payload["company_ref"] = {"id": args.company_id, "name": "Sofia EdTech", "key": "sofia"}

    url = f"{args.limbo_url.rstrip('/')}/api/v1/reports/ingest"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        print("OK:", json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
