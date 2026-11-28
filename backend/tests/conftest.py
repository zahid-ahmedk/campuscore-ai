import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["SECRET_KEY"] = "test-secret"
os.environ.pop("OPENAI_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

import seed
from database import Base, SessionLocal, engine
from main import app


@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed.seed_demo(db)
    db.close()
    return TestClient(app)


def login(client, email):
    r = client.post("/api/auth/login", json={"email": email, "password": seed.DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client): return login(client, "admin@quest-portal.local")
@pytest.fixture(scope="session")
def clerk(client): return login(client, "clerk@quest-portal.local")
@pytest.fixture(scope="session")
def student(client): return login(client, "21it95@quest-portal.local")
