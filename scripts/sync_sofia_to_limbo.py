import os
from sqlalchemy import create_engine, text
import uuid
from datetime import datetime, timedelta

# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════
# OPÇÃO SECUNDÁRIA — sync direto de banco (mesmo ambiente/rede).
# Fonte PRIMÁRIA recomendada: agentes da app enviam relatório JSON via
#   POST /api/v1/reports/ingest  (ver scripts/send_report_example.py)
# ══════════════════════════════════════════════════════════════════
SOFIA_DB_URL = "postgresql://user:pass@host:5432/sofia_db"
LIMBO_DB_URL = "postgresql://user:pass@localhost:5433/THE_LIMBO"
COMPANY_ID = "SEU-UUID-DA-SOFIA-NO-LIMBO" # ID da empresa "Sofia" dentro do Limbo

sofia_engine = create_engine(SOFIA_DB_URL)
limbo_engine = create_engine(LIMBO_DB_URL)

def sync_users_and_leads():
    """
    Sincroniza Alunos. 
    - Se tem assinatura ativa -> cs_customers (Cliente)
    - Se não tem -> growth_leads (Lead para Marketing trabalhar)
    """
    print("--- Sincronizando Alunos e Leads ---")
    with sofia_engine.connect() as s_conn, limbo_engine.connect() as l_conn:
        # Pega usuários e junta com XP atual
        query = text("""
            SELECT u.id, u.nome, u.email, u.status_assinatura, u.data_registro, 
                   COALESCE(xp.xp_total, 0) as xp
            FROM usuarios u
            LEFT JOIN user_xp xp ON u.id = xp.usuario_id
        """)
        alunos = s_conn.execute(query).fetchall()

        for aluno in alunos:
            is_active = aluno.status_assinatura in ['active', 'trial']
            
            if is_active:
                # É CLIENTE (CS)
                # Lógica simplificada de Health Score inicial baseada no XP acumulado
                initial_health = min(100, int(aluno.xp / 100)) 
                
                sql = text("""
                    INSERT INTO cs_customers (id, company_id, name, onboarding_status, health_score, external_source_id, last_xp_score)
                    VALUES (:id, :cid, :name, :status, :score, :ext_id, :xp)
                    ON CONFLICT (company_id, external_source_id) DO UPDATE SET
                    health_score = :score, last_xp_score = :xp
                """)
                l_conn.execute(sql, {
                    "id": uuid.uuid4(), "cid": COMPANY_ID, "name": aluno.nome,
                    "status": aluno.status_assinatura, "score": initial_health,
                    "ext_id": str(aluno.id), "xp": aluno.xp
                })
            else:
                # É LEAD (Marketing) - O usuário cadastrou mas não paga
                # Verificamos se já existe na tabela de leads
                sql_lead = text("""
                    INSERT INTO growth_leads (id, company_id, email, name, status, source_campaign_id, created_at)
                    VALUES (:id, :cid, :email, :name, 'nurturing', NULL, :reg_date)
                    ON CONFLICT DO NOTHING
                """)
                l_conn.execute(sql_lead, {
                    "id": uuid.uuid4(), "cid": COMPANY_ID, "email": aluno.email,
                    "name": aluno.nome, "reg_date": aluno.data_registro
                })
        l_conn.commit()

def sync_support_tickets():
    """
    Traz as dúvidas do 'support_threads' da Sofia para o 'cs_tickets' do Limbo.
    Isso permite que a IA analise quais são as maiores dores dos alunos.
    """
    print("--- Sincronizando Suporte ---")
    with sofia_engine.connect() as s_conn, limbo_engine.connect() as l_conn:
        # Busca threads atualizadas recentemente
        threads = s_conn.execute(text("SELECT id, user_id, title, status, created_at FROM support_threads")).fetchall()
        
        for t in threads:
            # Precisamos achar o ID do cliente no Limbo baseado no ID da Sofia
            customer = l_conn.execute(text("SELECT id FROM cs_customers WHERE external_source_id = :eid"), {"eid": str(t.user_id)}).fetchone()
            
            if customer:
                sql = text("""
                    INSERT INTO cs_tickets (id, customer_id, title, status, external_ticket_id, created_at)
                    VALUES (:id, :cust_id, :title, :status, :ext_id, :date)
                    ON CONFLICT DO NOTHING
                """)
                l_conn.execute(sql, {
                    "id": uuid.uuid4(), "cust_id": customer.id,
                    "title": t.title, "status": t.status,
                    "ext_id": str(t.id), "date": t.created_at
                })
        l_conn.commit()

def calculate_advanced_health_score():
    """
    O Diferencial: Cruza dados de Simulados (Engajamento) com Suporte (Problemas)
    """
    print("--- Calculando Health Score via IA/Dados ---")
    with sofia_engine.connect() as s_conn, limbo_engine.connect() as l_conn:
        customers = l_conn.execute(text(f"SELECT id, external_source_id FROM cs_customers WHERE company_id = '{COMPANY_ID}'")).fetchall()
        
        for c in customers:
            if not c.external_source_id: continue
            
            # 1. Engajamento: Quantos simulados nos últimos 7 dias?
            simulados = s_conn.execute(text("""
                SELECT COUNT(*) FROM simulados 
                WHERE usuario_id = :uid AND data_execucao > NOW() - INTERVAL '7 days'
            """), {"uid": int(c.external_source_id)}).scalar()
            
            # 2. Risco: Tem ticket aberto?
            open_tickets = s_conn.execute(text("""
                SELECT COUNT(*) FROM support_threads 
                WHERE user_id = :uid AND status != 'resolved'
            """), {"uid": int(c.external_source_id)}).scalar()
            
            # CÁLCULO DO SCORE (Base 50)
            score = 50
            score += (simulados * 5) # +5 pontos por simulado (Engajado)
            score -= (open_tickets * 10) # -10 pontos por problema aberto (Risco)
            
            # Limites
            score = max(0, min(100, score))
            
            # Atualiza no Limbo
            l_conn.execute(text("UPDATE cs_customers SET health_score = :s WHERE id = :id"), {"s": score, "id": c.id})
        
        l_conn.commit()

if __name__ == "__main__":
    sync_users_and_leads()
    sync_support_tickets() # Novo passo importante
    calculate_advanced_health_score() # Lógica revisada
    # (Adicionar aqui a sync_finance do exemplo anterior)