import json
import os
import sys
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["DB_URL"] = "sqlite:///./test_agents.db"
os.environ["SECRET_KEY"] = "test_secret"

sys.path.append(os.getcwd())
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
from app.modules.advisory import tools, schemas as advisory_schemas
from app.modules.agents import registry, models as agent_models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_agents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


class MockUser:
    def __init__(self, id, company_id, email):
        self.id = id
        self.company_id = company_id
        self.email = email


test_user = None


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
    db.query(agent_models.AgentAction).delete()
    db.query(agent_models.AgentOrchestrationRun).delete()
    db.query(User).delete()
    db.query(Company).delete()

    company_id = uuid.uuid4()
    db.add(Company(id=company_id, name="Startup A", created_at=datetime.now()))

    user_id = uuid.uuid4()
    test_user = MockUser(id=user_id, company_id=company_id, email="founder@test.com")

    db.add(User(
        id=user_id, company_id=company_id, full_name="Founder",
        email="founder@test.com", created_at=datetime.now(),
    ))
    db.commit()
    db.close()
    return company_id


def test_registry_lists_agents():
    agents = registry.list_agents()
    ids = {a["id"] for a in agents}
    assert "cfo" in ids
    assert "cmo" in ids
    assert "manager" in ids
    print("[OK] Registry test passed")


def test_tools_return_json():
    company_id = str(seed())
    stats = json.loads(tools._get_financial_stats(company_id))
    assert "total_balance" in stats
    assert "headcount" in stats

    roadmap = json.loads(tools._get_roadmap(company_id))
    assert isinstance(roadmap, list)
    print("[OK] Tools test passed")


def test_command_center_loads():
    seed()
    response = client.get("/api/v1/agents/command-center")
    assert response.status_code == 200
    assert "Command Center" in response.text
    assert "HI-C" in response.text
    print("[OK] Command Center UI test passed")


def test_registry_api():
    seed()
    response = client.get("/api/v1/agents/registry")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 6
    print("[OK] Registry API test passed")


@patch("app.modules.agents.manager.agent.run_agent", new_callable=AsyncMock)
def test_orchestration_api(mock_run_agent):
    seed()
    mock_run_agent.return_value = advisory_schemas.AdvisoryResponse(
        response="Análise mockada.",
        session_id="s1",
        tools_used=["get_runway"],
    )
    response = client.post(
        "/api/v1/agents/orchestrate",
        json={"objective": "Qual o runway da startup?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["objective"] == "Qual o runway da startup?"
    assert "synthesis" in data
    assert len(data["steps"]) == 4
    print("[OK] Orchestration API test passed")


if __name__ == "__main__":
    try:
        test_registry_lists_agents()
        test_tools_return_json()
        test_command_center_loads()
        test_registry_api()
        test_orchestration_api()
        print("\nAll Agent Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("./test_agents.db"):
            try:
                os.remove("./test_agents.db")
            except OSError:
                pass
