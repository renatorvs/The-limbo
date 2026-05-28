"""Phase 2 tests: skills, HI-C executor, multi-orchestration, tenant filtering."""

import json
import os
import sys
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

os.environ["OPENAI_API_KEY"] = "test"
os.environ["GOOGLE_API_KEY"] = "test"
os.environ["DB_URL"] = "sqlite:///./test_phase2.db"
os.environ["SECRET_KEY"] = "test"

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
from app.modules.advisory import schemas as advisory_schemas
from app.modules.agents import models as agent_models, skill_loader, action_executor
from app.modules.growth import models as growth_models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase2.db"
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


def seed_two_companies():
    global test_user
    db = TestingSessionLocal()
    db.query(agent_models.AgentAction).delete()
    db.query(growth_models.Campaign).delete()
    db.query(User).delete()
    db.query(Company).delete()

    co1 = uuid.uuid4()
    co2 = uuid.uuid4()
    db.add(Company(id=co1, name="Sofia EdTech", created_at=datetime.now()))
    db.add(Company(id=co2, name="Startup B", created_at=datetime.now()))

    user_id = uuid.uuid4()
    test_user = MockUser(id=user_id, company_id=co1, email="founder@test.com")
    db.add(User(id=user_id, company_id=co1, full_name="Founder", email="founder@test.com", created_at=datetime.now()))
    db.commit()
    db.close()
    return co1, co2


def test_skill_loader():
    skill = skill_loader.load_skill_for_agent("cfo")
    assert skill is not None
    assert "runway" in skill.lower() or "Workflow" in skill
    print("[OK] Skill loader")


def test_propose_write_action():
    co1, _ = seed_two_companies()
    from app.modules.advisory.tools import _propose_write_action

    result = json.loads(_propose_write_action(
        str(co1), "cmo", "create_campaign",
        "Campanha Google Ads Q2",
        '{"name": "Google Ads Q2", "channel": "google", "budget_total": 5000}',
    ))
    assert result["status"] == "pending_approval"
    assert "action_id" in result
    print("[OK] Propose write action")


def test_action_executor_create_campaign():
    co1, _ = seed_two_companies()
    db = TestingSessionLocal()
    action = agent_models.AgentAction(
        id=uuid.uuid4(),
        company_id=co1,
        agent_id="cmo",
        action_type="create_campaign",
        description="Test campaign",
        payload={"name": "Test Ads", "channel": "meta", "budget_total": 3000, "status": "Active"},
        status="pending",
    )
    db.add(action)
    db.commit()

    result = action_executor.execute_action(db, action)
    assert result["status"] == "created"
    db.close()
    print("[OK] Action executor create_campaign")


def test_tenant_filter_growth():
    co1, co2 = seed_two_companies()
    db = TestingSessionLocal()
    db.add(growth_models.Campaign(
        id=uuid.uuid4(), company_id=co1, name="Camp A", channel="google",
        status="Active", budget_total=1000,
    ))
    db.add(growth_models.Campaign(
        id=uuid.uuid4(), company_id=co2, name="Camp B", channel="meta",
        status="Active", budget_total=2000,
    ))
    db.commit()
    db.close()

    response = client.get("/api/v1/growth/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Camp A"
    print("[OK] Tenant filter growth campaigns")


@patch("app.modules.agents.manager.agent.run_agent", new_callable=AsyncMock)
def test_multi_orchestration(mock_run_agent):
    co1, co2 = seed_two_companies()
    mock_run_agent.return_value = advisory_schemas.AdvisoryResponse(
        response="Analise mock.", session_id="s1", tools_used=[],
    )
    response = client.post(
        "/api/v1/agents/orchestrate/multi",
        json={
            "objective": "Onde alocar capital?",
            "company_ids": [str(co1), str(co2)],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["companies"]) == 2
    assert "portfolio_synthesis" in data
    print("[OK] Multi orchestration API")


if __name__ == "__main__":
    try:
        test_skill_loader()
        test_propose_write_action()
        test_action_executor_create_campaign()
        test_tenant_filter_growth()
        test_multi_orchestration()
        print("\nAll Phase 2 Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("./test_phase2.db"):
            try:
                os.remove("./test_phase2.db")
            except OSError:
                pass
