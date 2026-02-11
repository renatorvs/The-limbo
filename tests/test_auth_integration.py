import sys
import os
sys.path.append(os.getcwd())
# Mock env vars
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"
os.environ["GOOGLE_API_KEY"] = "ai-test-key"
os.environ["DB_URL"] = "postgresql://user:pass@localhost/db"
os.environ["SECRET_KEY"] = "super-secret-key"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core import models

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_company_switching():
    # 1. Dev Login
    resp_login = client.post("/api/v1/auth/dev-login")
    assert resp_login.status_code == 200
    assert "access_token" in resp_login.json()
    token = resp_login.json()["access_token"]
    cookies = resp_login.cookies
    
    # 2. Create Company
    company_data = {
        "name": "Test Company",
        "industry": "Tech"
    }
    resp_create = client.post("/api/v1/backbone/companies", json=company_data, headers={"Authorization": f"Bearer {token}"})
    assert resp_create.status_code == 200
    company_id = resp_create.json()["id"]
    
    # 3. Switch Context
    resp_switch = client.post(f"/api/v1/auth/switch-context/{company_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_switch.status_code == 200
    assert resp_switch.json()["company_id"] == company_id
    
    print("✅ Auth and Switching Logic Validated")

if __name__ == "__main__":
    try:
        test_company_switching()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
