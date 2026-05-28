"""Tests for MVP Cockpit: KPIs, goals, prompts."""

import os
import sys
import uuid
from datetime import datetime

os.environ["OPENAI_API_KEY"] = "test"
os.environ["GOOGLE_API_KEY"] = "test"
os.environ["DB_URL"] = "sqlite:///./test_cockpit.db"
os.environ["SECRET_KEY"] = "test"

sys.path.append(os.getcwd())
from unittest.mock import MagicMock
sys.modules["langchain_google_genai"] = MagicMock()
sys.modules["langchain_google_genai.ChatGoogleGenerativeAI"] = MagicMock()
sys.modules["langchain_google_genai.GoogleGenerativeAIEmbeddings"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.models import Company, User
from app.core import security
from app.modules.cockpit import service, prompt_library, schemas

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cockpit.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

test_user = None


class MockUser:
    def __init__(self, id, company_id, email):
        self.id = id
        self.company_id = company_id
        self.email = email


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return test_user


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[security.get_current_user] = override_get_current_user
client = TestClient(app)


def seed():
    global test_user
    db = TestingSessionLocal()
    db.query(User).delete()
    db.query(Company).delete()
    co_id = uuid.uuid4()
    db.add(Company(id=co_id, name="Sofia MVP", created_at=datetime.now()))
    user_id = uuid.uuid4()
    test_user = MockUser(id=user_id, company_id=co_id, email="founder@test.com")
    globals()["test_user"] = test_user
    db.add(User(id=user_id, company_id=co_id, full_name="Founder", email="founder@test.com", created_at=datetime.now()))
    db.commit()
    db.close()
    return co_id


def test_prompt_suggestions_by_domain():
    cfo = prompt_library.get_suggestions("cfo")
    cmo = prompt_library.get_suggestions("cmo")
    assert len(cfo) >= 3
    assert len(cmo) >= 3
    assert "runway" in cfo[0]["prompt"].lower() or "Runway" in cfo[0]["label"]
    print("[OK] Prompt suggestions by domain")


def test_mvp_dashboard():
    co_id = seed()
    db = TestingSessionLocal()
    dash = service.get_mvp_dashboard(db, co_id)
    assert dash.company_name == "Sofia MVP"
    assert len(dash.domains) == 4
    assert dash.domains[0].domain == "cfo"
    db.close()
    print("[OK] MVP dashboard")


def test_quick_goal_update():
    co_id = seed()
    db = TestingSessionLocal()
    service.upsert_goal(db, co_id, schemas.MvpGoalUpdate(
        domain="cfo", metric_key="runway_months", target_value=18,
    ))
    dash = service.get_mvp_dashboard(db, co_id)
    runway = next(k for k in dash.domains[0].kpis if k.key == "runway_months")
    assert runway.target_value == 18
    db.close()
    print("[OK] Quick goal update")


def test_prompt_history_and_favorites():
    co_id = seed()
    db = TestingSessionLocal()
    service.log_prompt(db, test_user.id, co_id, "cmo", "Qual o CAC atual?")
    fav = service.add_favorite(db, test_user.id, schemas.PromptFavoriteCreate(
        agent_id="cmo", label="CAC check", prompt_text="Qual o CAC atual?",
    ))
    history = service.get_history(db, test_user.id, "cmo")
    favorites = service.get_favorites(db, test_user.id, "cmo")
    assert len(history) >= 1
    assert len(favorites) >= 1
    db.close()
    print("[OK] Prompt history and favorites")


def test_cockpit_ui():
    seed()
    response = client.get("/api/v1/cockpit/dashboard")
    assert response.status_code == 200
    assert "MVP Cockpit" in response.text
    assert "Runway" in response.text
    print("[OK] Cockpit UI")


def test_root_redirects_to_cockpit():
    seed()
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "cockpit" in response.headers.get("location", "")
    print("[OK] Root redirect")


if __name__ == "__main__":
    try:
        test_prompt_suggestions_by_domain()
        test_mvp_dashboard()
        test_quick_goal_update()
        test_prompt_history_and_favorites()
        test_cockpit_ui()
        test_root_redirects_to_cockpit()
        print("\nAll Cockpit Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("./test_cockpit.db"):
            try:
                os.remove("./test_cockpit.db")
            except OSError:
                pass
