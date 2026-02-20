"""API tests. Requires qcrypto for Phase B+."""
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_username() -> str:
    """Unique username for test isolation."""
    return f"test_{uuid.uuid4().hex[:12]}"


def test_health():
    """Smoke: GET /health returns 200 and status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_keys_generate():
    """POST /api/keys/generate requires auth, returns key ids."""
    r = client.post("/api/keys/generate")
    assert r.status_code == 401
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": username, "password": "secret123"})
    token = login_r.json()["token"]
    r = client.post("/api/keys/generate", headers={"Authorization": f"Bearer {token}"})
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
    """GET /api/keys/public returns keys for authenticated user (keys from register)."""
    r = client.get("/api/keys/public")
    assert r.status_code == 401
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": username, "password": "secret123"})
    token = login_r.json()["token"]
    r = client.get("/api/keys/public", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "kem_public_key" in data
    assert "sig_public_key" in data


def test_keys_public_by_id():
    """GET /api/keys/public/{id} returns another user's keys by id or username."""
    username = _unique_username()
    reg = client.post("/api/users/register", json={"username": username, "password": "secret123"})
    user_id = reg.json()["user_id"]
    r = client.get(f"/api/keys/public/{user_id}")
    assert r.status_code == 200
    assert r.json()["username"] == username
    assert "kem_public_key" in r.json()
    r2 = client.get("/api/keys/public/unknown_nonexistent_user")
    assert r2.status_code == 404


def test_users_register():
    """Register creates user and returns JWT."""
    username = _unique_username()
    r = client.post(
        "/api/users/register",
        json={"username": username, "password": "secret123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert "user_id" in data
    assert data["user_id"]  # non-empty
    # Duplicate username returns 400
    r2 = client.post(
        "/api/users/register",
        json={"username": username, "password": "other"},
    )
    assert r2.status_code == 400


def test_users_login():
    """Login returns JWT for valid creds, 401 for invalid."""
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    r = client.post(
        "/api/users/login",
        json={"username": username, "password": "secret123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert "user_id" in data
    r2 = client.post(
        "/api/users/login",
        json={"username": "nonexistent", "password": "x"},
    )
    assert r2.status_code == 401


def test_users_me():
    """GET /api/users/me returns current user when authenticated."""
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post(
        "/api/users/login",
        json={"username": username, "password": "secret123"},
    )
    token = login_r.json()["token"]
    r = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["username"] == username
    r2 = client.get("/api/users/me")
    assert r2.status_code == 401  # no auth


def test_models_upload():
    """Stub model upload."""
    r = client.post("/api/models/upload", files={"file": ("model.pt", b"fake model content")})
    assert r.status_code == 200
    assert "id" in r.json()
