import sys
import os
from unittest.mock import MagicMock, patch

# Set env vars BEFORE importing app.core.config
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["DB_URL"] = "sqlite:///./test_companies.db"
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
from datetime import datetime
import uuid

from app.main import app
from app.core.database import Base, get_db
from app.modules.backbone import schemas
from app.core.models import Company, User
from app.core import security

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_companies.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock User class
class MockUser:
    def __init__(self, id, company_id, email):
        self.id = id
        self.company_id = company_id
        self.email = email

test_user = None

def override_get_current_user():
    return test_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[security.get_current_user] = override_get_current_user

client = TestClient(app)

def test_create_and_list_companies():
    # 1. Create a Company
    payload = {
        "name": "New Tech Corp",
        "cnpj_or_tax_id": "123456789",
        "industry": "Software",
        "logo_url": "http://example.com/logo.png"
    }
    
    response = client.post("/api/v1/backbone/companies", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Tech Corp"
    assert "id" in data
    
    company_id = data["id"]
    
    # 2. List Companies
    response = client.get("/api/v1/backbone/companies")
    assert response.status_code == 200
    companies = response.json()
    
    assert len(companies) >= 1
    found = False
    for c in companies:
        if c["id"] == company_id:
            found = True
            assert c["name"] == "New Tech Corp"
            break
            
    assert found
    print("✅ Company Creation and Listing Test Passed")

if __name__ == "__main__":
    try:
        test_create_and_list_companies()
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("./test_companies.db"):
            try:
                os.remove("./test_companies.db")
            except:
                pass
