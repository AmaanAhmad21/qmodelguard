"""Basic API tests. No qcrypto required (stubs used)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """Smoke: GET /health returns 200 and status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_keys_generate():
    """Smoke: POST /api/keys/generate returns 200 and expected key fields."""
    r = client.post("/api/keys/generate")
    assert r.status_code == 200
    data = r.json()
    assert "kem_key_id" in data
    assert "sig_key_id" in data


def test_root():
    """Health check."""
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "QModelGuard"


def test_keys_public():
    """Stub get public keys."""
    r = client.get("/api/keys/public")
    assert r.status_code == 200


def test_keys_public_by_id():
    """Stub get public key by id."""
    r = client.get("/api/keys/public/1")
    assert r.status_code == 200
    r2 = client.get("/api/keys/public/unknown")
    assert r2.status_code == 404


def test_users_register():
    """Stub register."""
    r = client.post("/api/users/register", json={"username": "alice", "password": "secret"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_users_login():
    """Stub login."""
    r = client.post("/api/users/login", json={"username": "alice", "password": "secret"})
    assert r.status_code == 200
    r2 = client.post("/api/users/login", json={"username": "bad", "password": "x"})
    assert r2.status_code == 401


def test_models_upload():
    """Stub model upload."""
    r = client.post("/api/models/upload", files={"file": ("model.pt", b"fake model content")})
    assert r.status_code == 200
    assert "id" in r.json()
