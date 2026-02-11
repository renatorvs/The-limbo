import sys
import os
sys.path.append(os.getcwd())
# Mock env vars
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"
os.environ["GOOGLE_API_KEY"] = "ai-test-key"
os.environ["DB_URL"] = "sqlite:///./test_backbone.db" # Use a fresh DB for this test

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core import models as core_models
from app.modules.backbone import models as backbone_models # Explicit import to ensure registration? 
# Actually, let's see if app.main does it.

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_backbone.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_backbone_tables_exist():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"DEBUG: Found tables: {tables}")
    assert "backbone_bank_accounts" in tables
    assert "backbone_ledger" in tables

def test_backbone_flow():
    # 1. Login as Admin to get token
    # We need to reuse the auth logic or mock it.
    # Let's use the dev-login endpoint we created!
    resp = client.post("/api/v1/auth/dev-login")
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Company (if needed, but dev-login might not set company_id context?)
    # The models show company_id is nullable in some places or we need to switch context.
    # Let's create a company first.
    company_data = {"name": "Test Corp", "industry": "Tech"}
    resp = client.post("/api/v1/backbone/companies", json=company_data, headers=headers)
    if resp.status_code == 404: # Endpoint might be under /api/v1/something else?
        # Checked router.py, it is /api/v1/backbone/companies
        pass
    assert resp.status_code == 200, f"Create Company failed: {resp.text}"
    company_id = resp.json()["id"]
    
    # Switch context to this company
    client.post(f"/api/v1/auth/switch-context/{company_id}", headers=headers)

    # 3. Create Bank Account
    account_data = {
        "bank_name": "Test Bank",
        "account_type": "Checking",
        "current_balance": 1000.00,
        "currency": "BRL",
        "company_id": company_id # specific schema might need this or it takes from context?
        # Looking at schema BankAccountCreate, it has company_id: Optional[UUID]
        # Service just does **dict.
    }
    # We might need to manually inject company_id if the endpoint doesn't automatically from user context.
    # The current backbone/router.py create_bank_account just calls service.create_bank_account.
    # It does NOT appear to inject current_user.company_id.
    # This might be a missing feature in the existing backend!
    # Let's try passing it explicitly.
    resp = client.post("/api/v1/backbone/bank-accounts", json=account_data, headers=headers)
    assert resp.status_code == 200, f"Create Account failed: {resp.text}"
    account_id = resp.json()["id"]

    # 4. Create Transaction
    txn_data = {
        "transaction_date": "2023-01-01",
        "description": "Initial Deposit",
        "amount": 1000.0,
        "type": "revenue",
        "status": "PAID",
        "account_id": account_id,
        "company_id": company_id
    }
    resp = client.post("/api/v1/backbone/transaction", json=txn_data, headers=headers)
    assert resp.status_code == 200, f"Create Transaction failed: {resp.text}"

    # 5. Verify Dashboard Stats
    resp = client.get("/api/v1/backbone/dashboard", headers=headers)
    assert resp.status_code == 200
    assert "1000.0" in resp.text # Should be in the HTML

    print("✅ Backbone Module Verified")

if __name__ == "__main__":
    try:
        test_backbone_tables_exist()
        test_backbone_flow()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
