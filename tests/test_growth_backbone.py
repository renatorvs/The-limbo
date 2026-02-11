import sys
import os
sys.path.append(os.getcwd())
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"
os.environ["GOOGLE_API_KEY"] = "ai-test-key"
os.environ["DB_URL"] = "postgresql://user:pass@localhost/db" # Mock, won't be used as we mock DB session
os.environ["SECRET_KEY"] = "super-secret-key"

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db, Base, engine
from app.core.models import Company, AnalyticsSaasMetricsDaily
from app.modules.growth.models import Campaign, FunnelSnapshot
from app.modules.backbone.models import BankAccount, CostCenter, Ledger, Staff
import uuid
from datetime import date, datetime, timedelta

# Setup
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_gb.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_growth_dashboard():
    db = TestingSessionLocal()
    
    # 1. Setup Data
    company_id = uuid.uuid4()
    company = Company(id=company_id, name="Growth Test Corp", industry="Tech")
    db.add(company)
    
    # Metricas
    metrics = AnalyticsSaasMetricsDaily(
        company_id=company_id,
        reference_date=date.today(),
        arr=100000.0,
        ltv=5000.0,
        churn_rate_percent=2.5,
        nps_score=75,
        cac=200.0
    )
    db.add(metrics)
    
    # Campaign
    campaign = Campaign(
        company_id=company_id,
        name="Test Campaign",
        channel="Google",
        status="Active",
        budget_total=5000.0,
        start_date=date.today()
    )
    db.add(campaign)
    
    # Funnel
    funnel = FunnelSnapshot(
        company_id=company_id,
        date=date.today(),
        visitors=1000,
        leads=200,
        customers=10
    )
    db.add(funnel)
    db.commit()
    db.close()
    
    # 2. Test Dashboard
    resp = client.get("/api/v1/growth/dashboard")
    assert resp.status_code == 200
    assert "100000.0" in resp.text
    assert "75" in resp.text
    assert "Test Campaign" in resp.text
    assert "1000" in resp.text # Visitors

def test_backbone_dashboard_and_transaction():
    db = TestingSessionLocal()
    
    # 1. Setup Data
    company_id = uuid.uuid4()
    company = Company(id=company_id, name="Backbone Test Corp", industry="Finance")
    db.add(company)
    
    # Bank Account
    account_id = uuid.uuid4()
    account = BankAccount(
        id=account_id,
        company_id=company_id,
        bank_name="Test Bank",
        account_type="Checking",
        current_balance=50000.0,
        currency="BRL"
    )
    db.add(account)
    
    # Cost Center
    cc_id = uuid.uuid4()
    cc = CostCenter(
        id=cc_id,
        company_id=company_id,
        name="Engineering",
        code="ENG-01",
        budget_limit=10000.0
    )
    db.add(cc)
    
    # Staff
    staff = Staff(
        company_id=company_id,
        full_name="John Doe",
        job_title="Dev",
        department="Engineering",
        contract_type="CLT",
        salary_cost=5000.0,
        hired_at=date.today()
    )
    db.add(staff)
    db.commit()
    db.close()
    
    # 2. Test Transaction Create
    txn_data = {
        "transaction_date": str(date.today()),
        "description": "Server Cost",
        "amount": 100.0,
        "type": "opex",
        "is_recurring": True,
        "recurrence_period": "monthly",
        "status": "PAID",
        "cost_center_id": str(cc_id),
        "account_id": str(account_id)
    }
    
    resp_txn = client.post("/api/v1/backbone/transaction", json=txn_data)
    if resp_txn.status_code != 200:
        print(f"Transaction failed: {resp_txn.text}")
    assert resp_txn.status_code == 200
    
    # 3. Test Dashboard (should see stats and transaction)
    resp = client.get("/api/v1/backbone/dashboard")
    assert resp.status_code == 200
    assert "50000.0" in resp.text # Balance
    assert "100.0" in resp.text # Burn Rate logic might need check (it sums OPEX)
    assert "Server Cost" in resp.text
    
if __name__ == "__main__":
    try:
        test_growth_dashboard()
        test_backbone_dashboard_and_transaction()
        print("\n✅ All Integrated Tests Passed!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
