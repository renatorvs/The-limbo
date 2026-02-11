import sys
import os
from unittest.mock import MagicMock, patch

# Set env vars
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["DB_URL"] = "sqlite:///./test_backbone.db"
os.environ["SECRET_KEY"] = "test_secret"

# Add app to path
sys.path.append(os.getcwd())

# MOCK BEFORE IMPORT
sys.modules["langchain_google_genai"] = MagicMock()
sys.modules["langchain_google_genai.ChatGoogleGenerativeAI"] = MagicMock()
sys.modules["langchain_google_genai.GoogleGenerativeAIEmbeddings"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core import security

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_backbone.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock User
test_user = None
def override_get_current_user():
    return test_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[security.get_current_user] = override_get_current_user

client = TestClient(app)

def test_backbone_modules():
    # 1. Create Company
    company_payload = {
        "name": "Test Corp",
        "industry": "Finance"
    }
    resp = client.post("/api/v1/backbone/companies", json=company_payload)
    assert resp.status_code == 200
    company_id = resp.json()["id"]

    # 2. Create Bank Account
    bank_payload = {
        "bank_name": "Test Bank",
        "account_type": "Checking",
        "currency": "USD",
        "current_balance": 1000.00,
        "company_id": company_id
    }
    resp = client.post("/api/v1/backbone/bank-accounts", json=bank_payload)
    assert resp.status_code == 200
    assert resp.json()["bank_name"] == "Test Bank"

    # 3. List Bank Accounts
    resp = client.get("/api/v1/backbone/bank-accounts")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 4. Create Cost Center
    cc_payload = {
        "name": "Marketing",
        "code": "MKT-01",
        "budget_limit": 5000.00,
        "company_id": company_id
    }
    resp = client.post("/api/v1/backbone/costcenter", json=cc_payload)
    assert resp.status_code == 200
    assert resp.json()["code"] == "MKT-01"

    # 5. List Cost Centers
    resp = client.get("/api/v1/backbone/costcenter")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    
    print("✅ Backbone Modules Verification Passed")

if __name__ == "__main__":
    try:
        test_backbone_modules()
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
    finally:
        if os.path.exists("./test_backbone.db"):
            try:
                os.remove("./test_backbone.db")
            except:
                pass
