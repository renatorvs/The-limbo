"""Prompts sugeridos por área — foco MVP e ajuste rápido."""

PROMPT_SUGGESTIONS = {
    "cfo": [
        {"label": "Runway atual", "prompt": "Qual o runway em meses? Estamos acima ou abaixo da meta de 12 meses? O que cortar primeiro?"},
        {"label": "Burn vs receita", "prompt": "Compare burn rate com MRR. Quantos meses até break-even no ritmo atual?"},
        {"label": "Prioridade de corte", "prompt": "Se precisarmos reduzir 20% do burn este mês, quais cost centers cortar com menor impacto no MVP?"},
        {"label": "Unit economics", "prompt": "O CAC atual justifica o LTV? Quanto posso gastar em aquisição sem comprometer runway?"},
    ],
    "cmo": [
        {"label": "CAC saudável", "prompt": "O CAC atual está abaixo de R$150? Qual canal tem melhor LTV:CAC para MVP?"},
        {"label": "Funil bottleneck", "prompt": "Onde o funil trava (visitors→leads→clientes)? Qual etapa otimizar primeiro?"},
        {"label": "Campanha MVP", "prompt": "Sugira uma campanha de R$ 3k focada em conversão trial, com canal e mensagem para EdTech."},
        {"label": "Meta de leads", "prompt": "Estamos na meta de 200 leads/mês? Se não, quais 3 ações rápidas para corrigir?"},
    ],
    "cpo": [
        {"label": "Ativação", "prompt": "A taxa de ativação está acima de 40%? Quais features bloqueiam o aha moment?"},
        {"label": "Roadmap MVP", "prompt": "Priorize o roadmap com RICE: o que entregar nas próximas 2 semanas para validar PMF?"},
        {"label": "Saúde técnica", "prompt": "Uptime e bugs abertos: posso lançar feature nova ou devo estabilizar primeiro?"},
        {"label": "DAU crescendo", "prompt": "DAU está crescendo semana a semana? Se não, qual hipótese testar primeiro?"},
    ],
    "cs": [
        {"label": "Risco de churn", "prompt": "Quais clientes têm health score baixo ou tickets abertos? Plano de retenção em 48h."},
        {"label": "NPS MVP", "prompt": "NPS está acima de 50? O que os detratores reclamam e como corrigir rápido?"},
        {"label": "Expansão", "prompt": "Quais clientes ativos têm potencial de upgrade de plano este mês?"},
        {"label": "Onboarding", "prompt": "Onde clientes travam no onboarding? 3 fixes rápidos para reduzir churn precoce."},
    ],
    "ceo": [
        {"label": "Status semanal", "prompt": "Resumo executivo: runway, MRR, NPS, DAU. Top 3 riscos e top 3 ações desta semana."},
        {"label": "Alocar capital", "prompt": "Tenho R$ 10k este mês: investir em growth, produto ou CS? Justifique com dados."},
        {"label": "PMF check", "prompt": "Temos sinais de product-market fit? Quais métricas provam ou refutam?"},
    ],
}


def get_suggestions(agent_id: str) -> list:
    return PROMPT_SUGGESTIONS.get(agent_id.lower(), [])


def get_all_by_domain() -> dict:
    return PROMPT_SUGGESTIONS
