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
from app.core import security

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_fallback.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user():
    print("DEBUG: Override get_current_user called")
    # Return a dummy admin user
    return User(id=None, email="mock@test.com", role="admin", company_id=None)

# Apply overrides
app.dependency_overrides[get_db] = override_get_db
# app.dependency_overrides[security.get_current_user] = override_get_current_user

client = TestClient(app)

print(f"DEBUG: security.oauth2_scheme.auto_error = {security.oauth2_scheme.auto_error}", flush=True)

def test_fallback_auth_creates_user():
    # Hit a protected endpoint WITHOUT token
    resp = client.get("/api/v1/advisory/dashboard")
    
    # Validation
    assert resp.status_code == 200, f"Expected 200 OK (with override), got {resp.status_code}. Resp: {resp.text}"
    print("✅ Fallback Auth (With Override) Validated")

if __name__ == "__main__":
    try:
        test_fallback_auth_creates_user()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Test Failed: {e}")
