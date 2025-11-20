import os, sys
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "extra.db")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
os.environ["DB_URL"] = "sqlite:///" + TEST_DB_PATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fastapi.testclient import TestClient
from backend.main import app, Base, engine
Base.metadata.create_all(bind=engine)
client = TestClient(app, raise_server_exceptions=False)

def register(username="u1", password="pass", role="user"):
    return client.post("/register", json={"username": username, "password": password, "role": role})

def login(username="u1", password="pass"):
    return client.post("/login-json", json={"username": username, "password": password})

def token(username="u1", password="pass"):
    return login(username, password).json()["access_token"]

def test_invalid_login():
    r = login("nouser", "bad")
    assert r.status_code == 400


def test_unauthorized_policy_access():
    r = client.get("/policies")
    assert r.status_code == 401


def test_partial_patch():
    register("adminY", "pass", "admin")
    t = token("adminY")
    # create
    c = client.post("/policies", headers={"Authorization": f"Bearer {t}"}, json={"name": "Car", "details": "Full"})
    pid = c.json()["id"]
    # partial patch (only name)
    p = client.patch(f"/policies/{pid}", headers={"Authorization": f"Bearer {t}"}, json={"name": "CarPlus"})
    assert p.status_code == 200
    assert p.json()["name"] == "CarPlus"
    # ensure details unchanged
    assert p.json()["details"] == "Full"


def test_user_cannot_delete_other_policy():
    register("adminZ", "pass", "admin")
    t_admin = token("adminZ")
    c = client.post("/policies", headers={"Authorization": f"Bearer {t_admin}"}, json={"name": "Home", "details": "Std"})
    pid = c.json()["id"]
    register("userZ", "pass", "user")
    t_user = token("userZ")
    d = client.delete(f"/policies/{pid}", headers={"Authorization": f"Bearer {t_user}"})
    assert d.status_code == 403


def test_internal_server_error():
    """Trigger 500 using debug endpoint that raises exception"""
    r = client.get("/debug/error500")
    # FastAPI converts unhandled exceptions to 500
    assert r.status_code == 500
