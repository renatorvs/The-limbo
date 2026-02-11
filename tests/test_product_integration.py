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
from app.modules.product import models
from datetime import date

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_product.db"
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

def test_create_and_view_roadmap_item():
    item_data = {
        "title": "New Feature X",
        "description": "Description of X",
        "status": "backlog",
        "priority": "high",
        "strategic_goal": "Growth",
        "target_date": str(date.today())
    }
    
    # Create
    resp = client.post("/api/v1/product/roadmap", json=item_data)
    if resp.status_code != 200:
        print(f"❌ Creation Failed: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Feature X"
    assert "id" in data

    # View Dashboard
    resp_dash = client.get("/api/v1/product/dashboard")
    assert resp_dash.status_code == 200
    assert "New Feature X" in resp_dash.text
    
def test_create_and_view_metrics():
    metric_data = {
        "metric_name": "uptime",
        "value": 99.95,
        "measured_at": str(date.today())
    }
    
    # Create
    resp = client.post("/api/v1/product/active-users", json=metric_data)
    assert resp.status_code == 200
    
    # View Dashboard
    resp_dash = client.get("/api/v1/product/dashboard")
    assert resp_dash.status_code == 200
    assert "99.95" in resp_dash.text

if __name__ == "__main__":
    try:
        test_create_and_view_roadmap_item()
        test_create_and_view_metrics()
        print("\n✅ All Product Tests Passed!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
