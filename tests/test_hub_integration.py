"""Hub INPUT → LIMBO → OUTPUT tests."""

import os
import sys

os.environ["OPENAI_API_KEY"] = "test"
os.environ["GOOGLE_API_KEY"] = "test"
os.environ["DB_URL"] = "sqlite:///./test_hub.db"
os.environ["SECRET_KEY"] = "test"

sys.path.append(os.getcwd())
from unittest.mock import MagicMock
sys.modules["langchain_google_genai"] = MagicMock()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base

engine = create_engine("sqlite:///./test_hub.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_hub_products_seeded():
    r = client.get("/api/v1/hub/products")
    assert r.status_code == 200
    keys = {p["app_key"] for p in r.json()}
    assert "sofia-education" in keys
    assert "bodyvision" in keys
    print("[OK] Products seeded")


def test_sofia_input_output():
    sample = client.get("/api/v1/hub/samples/sofia-education").json()
    inp = client.post("/api/v1/hub/sofia-education/input", json=sample)
    assert inp.status_code == 200
    out = client.get("/api/v1/hub/sofia-education/output")
    assert out.status_code == 200
    data = out.json()
    assert data["app_key"] == "sofia-education"
    assert "briefing" in data
    print("[OK] Sofia INPUT -> OUTPUT")


def test_bodyvision_input_output():
    sample = client.get("/api/v1/hub/samples/bodyvision").json()
    inp = client.post("/api/v1/hub/bodyvision/input", json=sample)
    assert inp.status_code == 200
    out = client.get("/api/v1/hub/bodyvision/output")
    assert out.status_code == 200
    assert out.json()["product_name"] == "BodyVision.IA"
    print("[OK] BodyVision INPUT -> OUTPUT")


def test_hub_ui():
    r = client.get("/api/v1/hub/")
    assert r.status_code == 200
    assert "Sofia Education IA" in r.text
    assert "BodyVision" in r.text
    print("[OK] Hub UI")


if __name__ == "__main__":
    try:
        test_hub_products_seeded()
        test_sofia_input_output()
        test_bodyvision_input_output()
        test_hub_ui()
        print("\nAll Hub Tests Passed!")
    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("./test_hub.db"):
            try:
                os.remove("./test_hub.db")
            except OSError:
                pass
