# tests/test_api.py
import os, sys, pathlib, datetime, pytest
from passlib.hash import bcrypt
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool   # ← IMPORTANTE

# ─── define credenciais de teste ───────────────────────────────
os.environ["ADMIN_EMAIL"]    = "admin@sstm.app"
os.environ["TEST_PLAIN_PWD"] = "test123"
os.environ["ADMIN_PWD_HASH"] = bcrypt.hash(os.environ["TEST_PLAIN_PWD"])

# ─── add backend/ ao PYTHONPATH ────────────────────────────────
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import main as app_module  # importa app depois de setar envs

# ─── engine SQLite memória compartilhada ───────────────────────
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as s:
        yield s

app_module.app.dependency_overrides[app_module.get_session] = get_session
client = TestClient(app_module.app)

# ─── fixtures ──────────────────────────────────────────────────
@pytest.fixture(scope="session")
def token():
    r = client.post(
        "/login",
        params={"email": os.environ["ADMIN_EMAIL"], "password": os.environ["TEST_PLAIN_PWD"]},
    )
    assert r.status_code == 200
    return r.json()["access_token"]

def auth(tok): return {"Authorization": f"Bearer {tok}"}

# ─── testes ────────────────────────────────────────────────────
def test_full_cycle(token):
    gid = client.post("/groups", json={"name": "SSTM"}, headers=auth(token)).json()["id"]

    aid = client.post(f"/groups/{gid}/persons", json={"full_name": "Ana"},   headers=auth(token)).json()["id"]
    bid = client.post(f"/groups/{gid}/persons", json={"full_name": "Bruno"}, headers=auth(token)).json()["id"]
    
    evt = {"title": "dev-01", "starts_at": "2025-07-10 19:00:00"}

    eid = client.post(f"/groups/{gid}/events", json=evt, headers=auth(token)).json()["id"]

    client.post(f"/events/{eid}/attendance", params={"person_id": aid, "status": "ABSENT"},  headers=auth(token))
    client.post(f"/events/{eid}/attendance", params={"person_id": bid, "status": "PRESENT"}, headers=auth(token))

    assert client.get(f"/groups/{gid}/summary").status_code == 200

    assert client.delete(f"/events/{eid}",  headers=auth(token)).status_code == 204
    assert client.delete(f"/persons/{aid}", headers=auth(token)).status_code == 204
    assert client.delete(f"/groups/{gid}",  headers=auth(token)).status_code == 204

    assert client.get(f"/groups/{gid}/summary").json() == []

def test_auth_guard():
    # sem token → 403 retornado pelo HTTPBearer
    assert client.post("/groups", json={"name":"Foo"}).status_code == 403
