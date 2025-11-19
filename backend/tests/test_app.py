import os, sys
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "test.db")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
os.environ["DB_URL"] = "sqlite:///" + TEST_DB_PATH  # isolated test db
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fastapi.testclient import TestClient
from backend.main import app, Base, engine
from sqlalchemy.orm import Session

# Create tables for test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def register(username="user1", password="pass", role="user"):
    return client.post("/register", json={"username": username, "password": password, "role": role})

def login(username="user1", password="pass"):
    return client.post("/login-json", json={"username": username, "password": password})

def auth_token(username="user1", password="pass"):
    r = login(username, password)
    return r.json()["access_token"]

# --- Tests ---

def test_register_and_login():
    r = register("alice", "pass", "user")
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token
    l = login("alice", "pass")
    assert l.status_code == 200


def test_policy_crud_user():
    register("bob", "pass", "user")
    token = auth_token("bob")
    # Create policy
    c = client.post("/policies", headers={"Authorization": f"Bearer {token}"}, json={"name": "Life", "details": "Life coverage"})
    assert c.status_code == 200
    pid = c.json()["id"]
    # List policies
    lst = client.get("/policies", headers={"Authorization": f"Bearer {token}"})
    assert lst.status_code == 200
    assert any(p["id"] == pid for p in lst.json())
    # User cannot delete (needs admin)
    d = client.delete(f"/policies/{pid}", headers={"Authorization": f"Bearer {token}"})
    assert d.status_code == 403


def test_admin_edit_delete():
    register("adminX", "pass", "admin")
    token_admin = auth_token("adminX")
    # Create as admin
    c = client.post("/policies", headers={"Authorization": f"Bearer {token_admin}"}, json={"name": "Health", "details": "Health"})
    pid = c.json()["id"]
    # Patch
    p = client.patch(f"/policies/{pid}", headers={"Authorization": f"Bearer {token_admin}"}, json={"details": "Updated"})
    assert p.status_code == 200
    assert p.json()["details"] == "Updated"
    # Delete
    d = client.delete(f"/policies/{pid}", headers={"Authorization": f"Bearer {token_admin}"})
    assert d.status_code == 200
    # Confirm gone
    lst = client.get("/policies", headers={"Authorization": f"Bearer {token_admin}"})
    assert all(pol["id"] != pid for pol in lst.json())
