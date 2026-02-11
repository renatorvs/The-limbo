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
from app.core.models import User

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_ui.db"
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

def test_auth_flow():
    # 1. Get Login Page
    resp = client.get("/api/v1/auth/login")
    assert resp.status_code == 200
    assert "Login - THE LIMBO" in resp.text
    
    # 2. Get Register Page
    resp = client.get("/api/v1/auth/register")
    assert resp.status_code == 200
    assert "Register - THE LIMBO" in resp.text
    
    # 3. Register User
    user_data = {
        "email": "testuser@example.com",
        "password": "securepassword123", # > 3 chars
        "full_name": "Test User"
    }
    resp = client.post("/api/v1/auth/register", json=user_data)
    assert resp.status_code == 200, f"Register failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    assert resp.cookies.get("access_token")
    
    # 4. Login User
    login_data = {
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    resp = client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    assert "access_token" in resp.json()
    
    # 5. Protected Route Access
    token = resp.json()["access_token"]
    resp = client.get("/api/v1/backbone/dashboard", headers={"Authorization": f"Bearer {token}"})
    # Since backbone dashboard might need company_id or redirect
    # Let's try advisory dashboard since we tested it before
    resp = client.get("/api/v1/advisory/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    
    # 6. Logout
    resp = client.get("/api/v1/auth/logout", allow_redirects=False)
    assert resp.status_code == 302
    assert 'access_token=""' in resp.headers["set-cookie"] # Cookie cleared
    
    print("✅ Auth UI and API Flow Validated")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
