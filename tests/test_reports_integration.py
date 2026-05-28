"""Tests for report ingestion (primary data source)."""

import json
import os
import sys
import uuid
from datetime import datetime, date, timedelta

os.environ["OPENAI_API_KEY"] = "test"
os.environ["GOOGLE_API_KEY"] = "test"
os.environ["DB_URL"] = "sqlite:///./test_reports.db"
os.environ["SECRET_KEY"] = "test"

sys.path.append(os.getcwd())
from unittest.mock import MagicMock
sys.modules["langchain_google_genai"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.models import Company, User
from app.core import security
from app.modules.reports import schemas
from app.modules.cockpit import service as cockpit_service

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_reports.db"
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
    co_id = uuid.uuid4()
    db.query(User).delete()
    db.query(Company).delete()
    db.add(Company(id=co_id, name="Sofia EdTech", created_at=datetime.now()))
    user_id = uuid.uuid4()
    test_user = MockUser(id=user_id, company_id=co_id, email="f@test.com")
    globals()["test_user"] = test_user
    db.add(User(id=user_id, company_id=co_id, full_name="F", email="f@test.com", created_at=datetime.now()))
    db.commit()
    db.close()
    return co_id


def test_ingest_report():
    co_id = seed()
    payload = {
        "limbo_report_version": "1.0",
        "company_ref": {"id": str(co_id)},
        "source_app": "sofia",
        "generated_by_agent": "sofia-agent",
        "period": {"start": str(date.today() - timedelta(days=7)), "end": str(date.today())},
        "executive_summary": "Semana boa, MRR subiu.",
        "domains": {
            "cfo": {
                "metrics": {"runway_months": 14, "mrr": 15000},
                "highlights": ["Runway ok"],
                "risks": [],
                "recommendations": [],
            },
            "cs": {
                "metrics": {"nps_score": 60, "active_customers": 400},
                "highlights": [],
                "risks": [],
                "recommendations": [],
            },
        },
    }
    resp = client.post("/api/v1/reports/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics_extracted"] >= 2
    assert data["knowledge_indexed"] is True
    print("[OK] Ingest report")


def test_cockpit_uses_report_metrics():
    co_id = seed()
    payload = {
        "limbo_report_version": "1.0",
        "company_ref": {"id": str(co_id)},
        "source_app": "sofia",
        "domains": {
            "cfo": {"metrics": {"runway_months": 99}, "highlights": [], "risks": [], "recommendations": []},
        },
    }
    client.post("/api/v1/reports/ingest", json=payload)

    db = TestingSessionLocal()
    dash = cockpit_service.get_mvp_dashboard(db, co_id)
    runway = next(k for k in dash.domains[0].kpis if k.key == "runway_months")
    assert runway.current_value == 99
    db.close()
    print("[OK] Cockpit uses report metrics (primary)")


def test_get_latest_report():
    co_id = seed()
    client.post("/api/v1/reports/ingest", json={
        "company_ref": {"id": str(co_id)},
        "source_app": "test",
        "executive_summary": "Test summary",
        "domains": {"cfo": {"metrics": {"mrr": 5000}, "highlights": [], "risks": [], "recommendations": []}},
    })
    resp = client.get("/api/v1/reports/latest")
    assert resp.status_code == 200
    assert resp.json()["source_app"] == "test"
    print("[OK] Get latest report")


if __name__ == "__main__":
    try:
        test_ingest_report()
        test_cockpit_uses_report_metrics()
        test_get_latest_report()
        print("\nAll Report Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("./test_reports.db"):
            try:
                os.remove("./test_reports.db")
            except OSError:
                pass
