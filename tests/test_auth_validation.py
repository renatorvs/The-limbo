import sys
import os
sys.path.append(os.getcwd())
# Mock env vars
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"
os.environ["GOOGLE_API_KEY"] = "ai-test-key"
os.environ["DB_URL"] = "sqlite:///./test_auth_validation.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_validation.db"
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

def test_password_validation():
    # 1. Try Short Password
    user_data = {
        "email": "short@example.com",
        "password": "short", # < 8 chars
        "full_name": "Short Pass User"
    }
    resp = client.post("/api/v1/auth/register", json=user_data)
    assert resp.status_code == 422 # Validation Error
    assert "Password must be at least 8 characters long" in resp.text
    print("✅ Short password rejected")

    # 2. Try Valid Password
    user_data["password"] = "validpassword123"
    user_data["email"] = "valid@example.com"
    resp = client.post("/api/v1/auth/register", json=user_data)
    assert resp.status_code == 200
    print("✅ Valid password accepted")

if __name__ == "__main__":
    try:
        test_password_validation()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
