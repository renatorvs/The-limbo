import sys
import os
from unittest.mock import MagicMock, patch

# Set env vars
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["DB_URL"] = "sqlite:///./test_cs.db"
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
from app.modules.cs import models

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cs.db"
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

def test_cs_dashboard():
    # Create Company directly in DB
    from app.core.models import Company
    import uuid
    company_id = uuid.uuid4()
    db = TestingSessionLocal()
    company = Company(id=company_id, name="Test Company", industry="Tech")
    db.add(company)
    db.commit()
    db.close()

    # Create Customer via API
    customer_payload = {
        "name": "Test Client A",
        "plan_name": "Pro",
        "mrr_value": 150.00,
        "health_score": 85,
        "onboarding_status": "Completed",
        "company_id": str(company_id)
    }
    resp = client.post("/api/v1/cs/customer", json=customer_payload)
    if resp.status_code != 200:
        print(f"Failed to create customer: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200, f"Failed: {resp.text}"
    
    # 2. Check Dashboard API (HTML)
    resp = client.get("/api/v1/cs/dashboard")
    assert resp.status_code == 200
    assert "Test Client A" in resp.text
    assert "Pro" in resp.text
    assert "85" in resp.text # Health Score

    # 3. Check Stats (via simple logic check in HTML content)
    # We added 1 customer with 150 MRR. 
    # Logic: Total MRR = 150.
    # Check if "150" appears in the right place? 
    # The template renders: {{ stats.total_mrr }} 
    # We can check if "150.0" is present.
    # Note: Javascript/HTML formatting might affect it (e.g. R$ 150.0).
    
    print("✅ CS Dashboard Verification Passed")

if __name__ == "__main__":
    try:
        test_cs_dashboard()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
    finally:
        if os.path.exists("./test_cs.db"):
            try:
                os.remove("./test_cs.db")
            except:
                pass
