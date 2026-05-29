# THE-LIMBO

**Administrador multi-agente para múltiplas startups** — plataforma central que recebe relatórios das apps (Sofia Education IA, BodyVision.IA), consolida KPIs, orquestra agentes de negócio com **Human-in-the-Loop (HI-C)** e devolve briefings e ações aprovadas.

Monólito modular em **FastAPI + SQLAlchemy + PostgreSQL (pgvector)** com UI Jinja2 e integração **LangChain + Gemini/OpenAI**.

---

## Visão geral

O Limbo não substitui as apps de produto. Ele atua como **camada de inteligência administrativa**:

```
Sofia Education IA  ──INPUT (JSON)──►  LIMBO  ──OUTPUT (briefing + KPIs + ações)──►  Sofia
BodyVision.IA       ──INPUT (JSON)──►  LIMBO  ──OUTPUT (briefing + KPIs + ações)──►  BodyVision
```

Cada app mantém seu próprio ambiente e banco. A integração primária é via **relatórios JSON** enviados periodicamente por um agente interno da app (ex.: `sofia-weekly-agent`).

---

## Produtos registrados

| `app_key`         | Produto              | Setor      | Prioridades MVP                                      |
|-------------------|----------------------|------------|------------------------------------------------------|
| `sofia-education` | Sofia Education IA   | EdTech     | trial_conversion, activation_rate, nps_score, runway |
| `bodyvision`      | BodyVision.IA        | HealthTech | dau, trial_conversion, cac, churn_rate               |

No startup, o Limbo cria/atualiza automaticamente as empresas correspondentes (`Company.app_key`).

---

## Regras de negócio

### 1. Multi-tenant por startup

- Toda entidade operacional (finanças, growth, produto, CS, ações de agente) pertence a uma **`company_id`**.
- Usuários autenticados têm uma startup vinculada; rotas internas exigem empresa selecionada (`require_company_id`).
- Consultas de domínio filtram por `company_id` quando a coluna existe.
- Modo **multi-startup** permite orquestrar agentes em paralelo para **2 ou mais** empresas (`POST /api/v1/agents/orchestrate/multi`).

### 2. Fonte de dados dos KPIs (prioridade)

1. **Relatório JSON ingerido** (`CompanyReport` ativo) — **fonte primária**
2. **Banco local do Limbo** (backbone, growth, product, cs) — fallback
3. **Script de sync de DB externo** (`scripts/sync_sofia_to_limbo.py`) — secundário/opcional

O Cockpit e o Hub usam sempre essa ordem ao montar dashboards e alertas.

### 3. Ingestão de relatórios

- Formato: `limbo_report_version: "1.0"` com domínios `cfo`, `cmo`, `cpo`, `cs`.
- Cada novo relatório da mesma app **substitui** o anterior (`status: active → superseded`).
- Métricas são normalizadas via aliases (`report_format.METRIC_ALIASES`).
- O conteúdo é indexado na **base de conhecimento RAG** do Advisory.
- `actions_proposed` no JSON geram **`AgentAction` com status `pending`** (HI-C).

### 4. Hub INPUT → OUTPUT

**INPUT** (`POST /api/v1/hub/{app_key}/input`):

1. Resolve a empresa pelo `app_key`
2. Ingere o relatório
3. Gera pacote OUTPUT automaticamente

**OUTPUT** (`GET /api/v1/hub/{app_key}/output`):

- Briefing executivo
- Alertas de KPI fora do trilho (`at_risk`, `off_track`)
- Recomendações por domínio
- Ações aprovadas e pendentes de aprovação
- Snapshot de métricas e sugestões de ajuste de meta

A app consome o OUTPUT e confirma com `POST .../output/ack`. Apenas um OUTPUT fica `is_active` por produto.

### 5. Cockpit MVP

- Catálogo fixo de KPIs essenciais por área (CFO, CMO, CPO, CS).
- Metas editáveis por empresa (`MvpGoal`); defaults vêm do catálogo.
- Status calculado: `on_track` | `at_risk` | `off_track` | `no_data`.
- Saúde geral agregada para o dashboard (`/api/v1/cockpit/dashboard`).

### 6. Agentes e HI-C (Human-in-the-Loop)

| Agente    | Papel                                      |
|-----------|--------------------------------------------|
| **CFO**   | Runway, burn, caixa, MRR                   |
| **CMO**   | CAC, funil, campanhas, conversão           |
| **CPO**   | Roadmap, DAU, ativação, engenharia          |
| **CS**    | NPS, churn, tickets, health score          |
| **CEO**   | Síntese estratégica e priorização          |
| **Manager** | Orquestração multi-agente                |

**Fluxo HI-C:**

1. Agente (ou relatório externo) **propõe** uma ação → `AgentAction.status = pending`
2. Humano **aprova** ou **rejeita** no Command Center
3. Se aprovada, o **action executor** persiste no módulo de domínio

**Ações executáveis hoje:**

| `action_type`       | Efeito                          |
|---------------------|---------------------------------|
| `create_campaign`   | Nova campanha em Growth         |
| `create_roadmap`    | Item no roadmap de Produto      |
| `move_roadmap`      | Altera status de item existente |
| `create_transaction`| Lançamento no ledger (Backbone) |
| `create_customer`   | Cliente em Customer Success     |
| `strategic_decision`| Registro de decisão (sem write) |

Nenhuma escrita destrutiva ou financeira ocorre **sem aprovação humana**.

### 7. Skills por domínio

Prompts enriquecidos com arquivos em `app/skills/` (CFO, CMO, CPO, CS, CEO, Manager), inspirados em práticas de [claude-skills](https://github.com/alirezarezvani/claude-skills).

### 8. Advisory (chat)

- Chat por persona com **tool-calling** real (leitura de KPIs scoped por `company_id`).
- Sidebar com sugestões de prompt, histórico e favoritos por área.

---

## Arquitetura de módulos

```
app/
├── core/           # Config, DB, security, tenant, models base
├── skills/         # Skills markdown por agente
├── modules/
│   ├── auth/       # Autenticação JWT
│   ├── backbone/   # Finanças e operações
│   ├── growth/     # Marketing e campanhas
│   ├── product/    # Roadmap e engenharia
│   ├── cs/         # Customer Success
│   ├── advisory/   # Chat IA + tools + RAG
│   ├── agents/     # Orquestração multi-agente + HI-C
│   ├── cockpit/    # Dashboard MVP + metas + prompts
│   ├── reports/    # Ingestão de relatórios JSON
│   └── hub/          # INPUT/OUTPUT Sofia + BodyVision
├── templates/      # UI Jinja2
scripts/            # Clientes CLI e sync secundário
tests/              # Testes de integração por fase
alembic/            # Migrações
```

---

## Interfaces principais

### UI (browser)

| Rota                              | Descrição                    |
|-----------------------------------|------------------------------|
| `/`                               | Redireciona para Cockpit     |
| `/api/v1/cockpit/dashboard`       | Dashboard MVP de KPIs        |
| `/api/v1/agents/command-center`   | HI-C — aprovar/rejeitar ações|
| `/api/v1/hub/`                    | Painel INPUT/OUTPUT          |
| `/api/v1/advisory/`               | Chat com agentes             |
| `/glossary`                       | Glossário de termos          |

### API Hub

```
POST /api/v1/hub/sofia-education/input
GET  /api/v1/hub/sofia-education/output
POST /api/v1/hub/sofia-education/output/ack

POST /api/v1/hub/bodyvision/input
GET  /api/v1/hub/bodyvision/output
POST /api/v1/hub/bodyvision/output/ack

GET  /api/v1/hub/samples/{app_key}   # Exemplo de JSON de INPUT
GET  /api/v1/hub/status              # Status dos produtos
```

### API Reports (alternativa genérica ao Hub)

```
POST /api/v1/reports/ingest          # Ingestão direta de AppReportIngest
```

### API Agents

```
POST /api/v1/agents/orchestrate       # Orquestração single-startup
POST /api/v1/agents/orchestrate/multi # Orquestração 2+ startups
POST /api/v1/agents/actions/{id}/resolve  # Aprovar/rejeitar ação
GET  /api/v1/agents/actions/pending
GET  /api/v1/agents/registry
```

Documentação interativa: `http://localhost:8000/docs`

---

## Formato do relatório (INPUT)

Exemplo mínimo — ver amostra completa em `GET /api/v1/hub/samples/sofia-education`:

```json
{
  "limbo_report_version": "1.0",
  "company_ref": { "key": "sofia-education", "name": "Sofia Education IA" },
  "source_app": "sofia-education",
  "generated_by_agent": "sofia-weekly-agent",
  "period": { "start": "2026-05-17", "end": "2026-05-24" },
  "executive_summary": "Resumo executivo da semana...",
  "domains": {
    "cfo": {
      "metrics": { "runway_months": 14, "monthly_burn": 45000, "mrr": 12000 },
      "highlights": ["..."],
      "risks": ["..."],
      "recommendations": ["..."]
    },
    "cmo": { "metrics": { "cac": 120, "trial_conversion": 18 }, "..." : "..." },
    "cpo": { "..." : "..." },
    "cs":  { "..." : "..." }
  },
  "actions_proposed": [
    {
      "agent_id": "cmo",
      "action_type": "create_campaign",
      "description": "Campanha de retenção plano básico",
      "payload": { "name": "Retenção Q2", "channel": "email", "budget_total": 5000 }
    }
  ]
}
```

---

## Setup

### Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ com extensões `uuid-ossp` e `vector`
- Chave de API Google (Gemini) ou OpenAI

### Instalação

```bash
pip install -r requirements.txt
```

### Variáveis de ambiente (`.env`)

```env
DB_URL=postgresql://user:pass@localhost:5432/the_limbo
SECRET_KEY=sua-chave-secreta-jwt
GOOGLE_API_KEY=sua-chave-gemini
OPENAI_API_KEY=sua-chave-openai   # opcional
```

### Executar

```bash
uvicorn app.main:app --reload
```

As tabelas são criadas no startup (`Base.metadata.create_all`). Produtos hub são seedados automaticamente.

### Scripts úteis

```bash
# Enviar INPUT de exemplo e ler OUTPUT
python scripts/hub_client.py sofia-education --action sample
python scripts/hub_client.py sofia-education --action input
python scripts/hub_client.py sofia-education --action output

# Sync secundário (se apps compartilharem DB — opcional)
python scripts/sync_sofia_to_limbo.py
python scripts/send_report_example.py
```

### Testes

```bash
pytest tests/test_hub_integration.py
pytest tests/test_reports_integration.py
pytest tests/test_agents_integration.py
pytest tests/test_cockpit_integration.py
pytest tests/test_phase2_integration.py
```

---

## Fluxo recomendado para integrar uma app

1. Implementar um **agente reporter** na app que gera o JSON semanal/mensal.
2. Enviar para `POST /api/v1/hub/{app_key}/input`.
3. Consumir `GET /api/v1/hub/{app_key}/output` e aplicar briefing/recomendações na app.
4. Confirmar consumo com `POST .../output/ack`.
5. (Opcional) Exibir ações pendentes na app ou aprovar no Command Center do Limbo.

---

## Roadmap conhecido

- Autenticação por API key nos endpoints de Hub/Reports
- Agente reporter embutido nas apps Sofia e BodyVision
- MCP Server para integração com Cursor/OpenClaw
- Sync automático de skills externas

---

## Licença

Projeto privado — Sofia Education IA / The Limbo.
