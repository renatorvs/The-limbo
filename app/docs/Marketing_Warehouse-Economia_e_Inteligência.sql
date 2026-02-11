Marketing_Warehouse: Economia_e_Inteligência.sql
Essa é uma jogada de mestre para economizar. Ferramentas que consolidam dados de Marketing (como Supermetrics, DashGoo ou HubSpot Marketing) custam caro (facilmente R$ 500 a R$ 2.000/mês).

Construindo isso no **The Limbo**, você terá um **"Marketing Warehouse"** próprio, sem mensalidade.

Para isso funcionar, precisamos transformar o módulo `Growth` do The Limbo. Atualmente, ele tem `growth_campaigns` e `growth_funnel_snapshot`, que são estáticos. Precisamos de **profundidade histórica** (saber quanto gastou *ontem* vs *hoje*).

Aqui está o plano de batalha técnico.

---

### Passo 1: Atualizar o Banco de Dados (Schema)

Seu banco atual guarda a campanha, mas não guarda o desempenho diário (Cliques, Impressões, CPC). Se você apenas atualizar a tabela `growth_campaigns`, você perde o histórico.

Vamos criar uma tabela de **Performance Diária**. Rode isso no seu PostgreSQL (The Limbo):

```sql
-- 1. Preparar a tabela de Campanhas para vincular com as APIs
ALTER TABLE growth_campaigns 
ADD COLUMN IF NOT EXISTS external_platform_id TEXT, -- ID da Campanha no Google/Meta
ADD COLUMN IF NOT EXISTS platform_account_id TEXT; -- ID da Conta de Anúncio

-- Índice para busca rápida na sincronização
CREATE INDEX IF NOT EXISTS idx_growth_ext_id ON growth_campaigns(external_platform_id);

-- 2. NOVA TABELA: Performance Diária (O segredo da economia)
-- Aqui guardamos o histórico dia a dia. Isso substitui o Supermetrics.
CREATE TABLE growth_daily_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    campaign_id UUID REFERENCES growth_campaigns(id),
    
    reference_date DATE NOT NULL,
    
    -- Métricas de Topo de Funil
    impressions INT DEFAULT 0,
    clicks INT DEFAULT 0,
    spend DECIMAL(10, 2) DEFAULT 0.00, -- Quanto gastou no dia
    
    -- Métricas Calculadas (Opcional, mas útil ter cacheado)
    cpc DECIMAL(10, 2), -- Custo por Clique
    ctr DECIMAL(5, 2), -- Taxa de Clique
    
    -- Conversões (Opcional, se a plataforma mandar)
    platform_conversions INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(campaign_id, reference_date) -- Garante que não duplica dados do mesmo dia
);

```

---

### Passo 2: Obter as Credenciais (A parte chata, mas necessária)

Para o script funcionar, você precisa gerar chaves de API nas plataformas.

1. **Google Ads:**
* Você precisa de um **Developer Token** (Pode pedir acesso "Basic" que é gratuito/rápido).
* Precisa configurar um **OAuth Client** no Google Cloud Console.
* *Meta:* Conseguir o `client_id`, `client_secret` e `refresh_token`.


2. **Meta (Facebook) Ads:**
* Crie um App no **Meta for Developers**.
* Adicione o produto "Marketing API".
* Gere um **System User Access Token** (Token permanente) para não precisar logar todo dia.



---

### Passo 3: O Script de Sincronização (`scripts/sync_marketing.py`)

Este script Python fará o trabalho pesado: vai nas APIs, baixa os dados de ontem e salva no The Limbo.

**Bibliotecas necessárias:**
`pip install google-ads facebook_business sqlalchemy psycopg2-binary`

```python
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import uuid
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from google.ads.googleads.client import GoogleAdsClient

# --- CONFIGURAÇÕES ---
LIMBO_DB_URL = "postgresql://user:pass@localhost:5433/THE_LIMBO"
COMPANY_ID = "SEU-UUID-DA-SOFIA"

# Credenciais META
META_APP_ID = 'seu_app_id'
META_APP_SECRET = 'seu_app_secret'
META_ACCESS_TOKEN = 'seu_token_permanente'
META_AD_ACCOUNT_ID = 'act_123456789' # O ID da sua conta de anúncios

# Credenciais GOOGLE (Geralmente carregado de um google-ads.yaml)
GOOGLE_ADS_CUSTOMER_ID = '123-456-7890'

engine = create_engine(LIMBO_DB_URL)

def sync_meta_ads():
    print("--- Sincronizando Meta Ads ---")
    FacebookAdsApi.init(META_APP_ID, META_APP_SECRET, META_ACCESS_TOKEN)
    
    # Pega dados de ONTEM (O dia fechado é sempre mais preciso)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    fields = ['campaign_name', 'campaign_id', 'spend', 'impressions', 'clicks', 'cpc', 'ctr']
    params = {
        'time_range': {'since': yesterday, 'until': yesterday},
        'level': 'campaign'
    }
    
    account = AdAccount(META_AD_ACCOUNT_ID)
    insights = account.get_insights(fields=fields, params=params)

    with engine.connect() as conn:
        for item in insights:
            # 1. Garante que a Campanha existe no Limbo
            # (Se criarmos campanha nova no Facebook, o Limbo aprende sozinho)
            check_camp = conn.execute(text("SELECT id FROM growth_campaigns WHERE external_platform_id = :eid"), {"eid": item['campaign_id']}).fetchone()
            
            if not check_camp:
                camp_id = uuid.uuid4()
                conn.execute(text("""
                    INSERT INTO growth_campaigns (id, company_id, name, channel, status, external_platform_id, start_date)
                    VALUES (:id, :cid, :name, 'Meta Ads', 'active', :eid, :date)
                """), {
                    "id": camp_id, "cid": COMPANY_ID, "name": item['campaign_name'], 
                    "eid": item['campaign_id'], "date": yesterday
                })
            else:
                camp_id = check_camp.id

            # 2. Insere a Performance do Dia
            conn.execute(text("""
                INSERT INTO growth_daily_performance 
                (id, company_id, campaign_id, reference_date, impressions, clicks, spend, cpc, ctr)
                VALUES (:id, :cid, :camp_id, :date, :imps, :clicks, :spend, :cpc, :ctr)
                ON CONFLICT (campaign_id, reference_date) DO UPDATE SET
                spend = :spend, clicks = :clicks, impressions = :imps
            """), {
                "id": uuid.uuid4(), "cid": COMPANY_ID, "camp_id": camp_id,
                "date": yesterday,
                "imps": item.get('impressions', 0),
                "clicks": item.get('clicks', 0),
                "spend": item.get('spend', 0),
                "cpc": item.get('cpc', 0),
                "ctr": item.get('ctr', 0)
            })
        conn.commit()

def sync_google_ads():
    print("--- Sincronizando Google Ads ---")
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    query = f"""
        SELECT 
          campaign.id, 
          campaign.name, 
          metrics.cost_micros, 
          metrics.clicks, 
          metrics.impressions, 
          metrics.ctr 
        FROM campaign 
        WHERE segments.date = '{yesterday}'
    """

    request = client.get_type("SearchGoogleAdsStreamRequest")
    request.customer_id = GOOGLE_ADS_CUSTOMER_ID
    request.query = query
    
    stream = ga_service.search_stream(request)

    with engine.connect() as conn:
        for batch in stream:
            for row in batch.results:
                campaign_id_str = str(row.campaign.id)
                spend_real = row.metrics.cost_micros / 1000000 # Google manda em micros

                # 1. Verifica/Cria Campanha
                check_camp = conn.execute(text("SELECT id FROM growth_campaigns WHERE external_platform_id = :eid"), {"eid": campaign_id_str}).fetchone()
                
                if not check_camp:
                    camp_id = uuid.uuid4()
                    conn.execute(text("""
                        INSERT INTO growth_campaigns (id, company_id, name, channel, status, external_platform_id, start_date)
                        VALUES (:id, :cid, :name, 'Google Ads', 'active', :eid, :date)
                    """), {
                        "id": camp_id, "cid": COMPANY_ID, "name": row.campaign.name, 
                        "eid": campaign_id_str, "date": yesterday
                    })
                else:
                    camp_id = check_camp.id

                # 2. Insere Performance
                conn.execute(text("""
                    INSERT INTO growth_daily_performance 
                    (id, company_id, campaign_id, reference_date, impressions, clicks, spend, ctr)
                    VALUES (:id, :cid, :camp_id, :date, :imps, :clicks, :spend, :ctr)
                    ON CONFLICT (campaign_id, reference_date) DO UPDATE SET
                    spend = :spend, clicks = :clicks
                """), {
                    "id": uuid.uuid4(), "cid": COMPANY_ID, "camp_id": camp_id,
                    "date": yesterday,
                    "imps": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "spend": spend_real,
                    "ctr": row.metrics.ctr
                })
        conn.commit()

if __name__ == "__main__":
    try:
        sync_meta_ads()
        sync_google_ads()
        print("Sincronização de Marketing Concluída!")
    except Exception as e:
        print(f"Erro na sincronização: {e}")

```

---

### Passo 4: O Valor Gerado (Visualização & IA)

Agora que os dados estão caindo no `growth_daily_performance`, você pode fazer coisas que ferramentas pagas cobram extra para fazer:

**1. Cálculo Automático de CAC Real**
Seu `analytics_saas_metrics_daily` tem um campo `cac`. Agora você pode atualizá-lo com precisão cirúrgica:

```sql
-- Query que o The Limbo roda para calcular o CAC de ontem
UPDATE analytics_saas_metrics_daily
SET cac = (
    SELECT SUM(spend) / NULLIF(leads, 0) -- Custo Total / Novos Leads
    FROM growth_daily_performance
    WHERE reference_date = CURRENT_DATE - 1
)
WHERE reference_date = CURRENT_DATE - 1;

```

**2. IA "Gestora de Tráfego"**
Como o módulo **Advisory** tem acesso ao banco, você pode perguntar ao seu chat:

> *"Qual campanha do Google teve o melhor CPC ontem e qual devo pausar?"*

A IA vai fazer um `SELECT` na tabela nova, ver qual gastou muito e teve pouco clique, e te responder com dados reais.

**Próximo passo:** Você já tem conta de desenvolvedor no Meta ou Google? Se não, recomendo começar pegando o **Token da Meta** primeiro, pois é menos burocrático que o do Google.