import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import uuid
# Note: These imports require the packages to be installed
# pip install google-ads facebook_business sqlalchemy psycopg2-binary
try:
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights
except ImportError:
    print("Warning: facebook_business not installed. Meta sync will fail.")

try:
    from google.ads.googleads.client import GoogleAdsClient
except ImportError:
    print("Warning: google-ads not installed. Google sync will fail.")

# --- CONFIGURAÇÕES ---
# Using environment variable for DB URL if available, else default
LIMBO_DB_URL = os.getenv("LIMBO_DB_URL", "postgresql://user:pass@localhost:5433/THE_LIMBO")
COMPANY_ID = os.getenv("COMPANY_ID", "SEU-UUID-DA-SOFIA")

# Credenciais META
META_APP_ID = os.getenv("META_APP_ID", 'seu_app_id')
META_APP_SECRET = os.getenv("META_APP_SECRET", 'seu_app_secret')
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", 'seu_token_permanente')
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", 'act_123456789')

# Credenciais GOOGLE
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", '123-456-7890')
GOOGLE_ADS_YAML_PATH = os.getenv("GOOGLE_ADS_YAML_PATH", "google-ads.yaml")

engine = create_engine(LIMBO_DB_URL)

def sync_meta_ads():
    print("--- Sincronizando Meta Ads ---")
    try:
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

        if not insights:
            print("Nenhum dado encontrado para Meta Ads ontem.")
            return

        with engine.connect() as conn:
            for item in insights:
                # 1. Garante que a Campanha existe no Limbo
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
                    print(f"Nova campanha Meta criada: {item['campaign_name']}")
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
            print("Dados Meta Ads sincronizados.")
            
    except Exception as e:
        print(f"Erro ao sincronizar Meta Ads: {e}")

def sync_google_ads():
    print("--- Sincronizando Google Ads ---")
    if not os.path.exists(GOOGLE_ADS_YAML_PATH):
        print(f"Arquivo {GOOGLE_ADS_YAML_PATH} não encontrado. Pulando Google Ads.")
        return

    try:
        client = GoogleAdsClient.load_from_storage(GOOGLE_ADS_YAML_PATH)
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
                        print(f"Nova campanha Google criada: {row.campaign.name}")
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
            print("Dados Google Ads sincronizados.")

    except Exception as e:
        print(f"Erro ao sincronizar Google Ads: {e}")

if __name__ == "__main__":
    print("Iniciando sincronização de marketing...")
    sync_meta_ads()
    sync_google_ads()
    print("Concluído.")
