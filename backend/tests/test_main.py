"""API tests. Requires qcrypto for Phase B+."""
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_username() -> str:
    """Unique username for test isolation."""
    return f"test_{uuid.uuid4().hex[:12]}"


def test_health():
    """GET /health returns 200 with status, database, storage."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert data.get("database") == "ok"
    assert "storage" in data
    assert data.get("storage") in ("ok", "missing")


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
    """Upload model requires auth, enforces extension/size, and returns real id."""
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": username, "password": "secret123"})
    token = login_r.json()["token"]

    r = client.post(
        "/api/models/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("model.pt", b"fake model content")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    model_id = data["id"]

    r2 = client.get(
        f"/api/models/{model_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.content == b"fake model content"

    # Disallow bad extension
    r_bad_ext = client.post(
        "/api/models/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("model.txt", b"bad content")},
    )
    assert r_bad_ext.status_code == 400


def test_models_list():
    """GET /api/models requires auth, returns paginated list with total, items (id, filename, is_encrypted, created_at)."""
    r = client.get("/api/models")
    assert r.status_code == 401
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": username, "password": "secret123"})
    token = login_r.json()["token"]
    # Empty list
    r = client.get("/api/models", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "total" in data and "items" in data and "limit" in data and "offset" in data
    assert data["total"] == 0
    assert data["items"] == []
    # After upload
    client.post(
        "/api/models/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("a.pt", b"x")},
    )
    r = client.get("/api/models", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert len(r.json()["items"]) == 1
    assert r.json()["items"][0]["filename"] == "a.pt"
    assert "is_encrypted" in r.json()["items"][0]
    assert "created_at" in r.json()["items"][0]


def test_models_list_pagination_validation():
    """GET /api/models with invalid limit/offset returns 400."""
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": username, "password": "secret123"})
    token = login_r.json()["token"]
    r = client.get("/api/models?limit=0", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    r = client.get("/api/models?offset=-1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400


def test_users_list():
    """GET /api/users/list requires auth, returns items with id and username."""
    r = client.get("/api/users/list")
    assert r.status_code == 401
    u1 = _unique_username()
    u2 = _unique_username()
    client.post("/api/users/register", json={"username": u1, "password": "secret123"})
    client.post("/api/users/register", json={"username": u2, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": u1, "password": "secret123"})
    token = login_r.json()["token"]
    r = client.get("/api/users/list", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    usernames = {x["username"] for x in data["items"]}
    assert u1 in usernames and u2 in usernames
    for item in data["items"]:
        assert "id" in item and "username" in item


def test_models_get_404_403():
    """GET /api/models/{id} returns 404 for missing id, 403 for not owner."""
    owner = _unique_username()
    other = _unique_username()
    client.post("/api/users/register", json={"username": owner, "password": "secret123"})
    client.post("/api/users/register", json={"username": other, "password": "secret123"})
    owner_token = (client.post("/api/users/login", json={"username": owner, "password": "secret123"})).json()["token"]
    other_token = (client.post("/api/users/login", json={"username": other, "password": "secret123"})).json()["token"]
    up = client.post(
        "/api/models/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("m.pt", b"data")},
    )
    model_id = up.json()["id"]
    r404 = client.get("/api/models/99999", headers={"Authorization": f"Bearer {owner_token}"})
    assert r404.status_code == 404
    r403 = client.get(f"/api/models/{model_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert r403.status_code == 403
    r400 = client.get("/api/models/notanint", headers={"Authorization": f"Bearer {owner_token}"})
    assert r400.status_code == 400


def test_models_delete():
    """DELETE /api/models/{id} requires auth and ownership; removes model and returns deleted id."""
    username = _unique_username()
    client.post("/api/users/register", json={"username": username, "password": "secret123"})
    login_r = client.post("/api/users/login", json={"username": username, "password": "secret123"})
    token = login_r.json()["token"]
    up = client.post(
        "/api/models/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("delme.pt", b"x")},
    )
    model_id = up.json()["id"]
    r = client.delete(f"/api/models/{model_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json().get("deleted") == model_id
    r2 = client.get(f"/api/models/{model_id}", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 404
    # Delete nonexistent -> 404
    r3 = client.delete("/api/models/99999", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 404


def test_models_encrypt_decrypt_sign_verify_flow():
    """Basic flow using stub crypto: encrypt -> decrypt -> sign -> verify."""
    # Sender and recipient
    sender = _unique_username()
    recipient = _unique_username()
    client.post("/api/users/register", json={"username": sender, "password": "secret123"})
    client.post("/api/users/register", json={"username": recipient, "password": "secret123"})

    sender_login = client.post("/api/users/login", json={"username": sender, "password": "secret123"})
    sender_token = sender_login.json()["token"]
    recipient_login = client.post("/api/users/login", json={"username": recipient, "password": "secret123"})
    recipient_token = recipient_login.json()["token"]

    # Upload by sender
    up = client.post(
        "/api/models/upload",
        headers={"Authorization": f"Bearer {sender_token}"},
        files={"file": ("m.pt", b"hello world")},
    )
    model_id = int(up.json()["id"])

    # Encrypt for recipient (stores encrypted model under recipient)
    enc = client.post(
        "/api/models/encrypt",
        headers={"Authorization": f"Bearer {sender_token}"},
        json={"model_id": model_id, "recipient_id": recipient},
    )
    assert enc.status_code == 200
    enc_id = int(enc.json()["encrypted_model_id"])

    # Recipient can download encrypted blob
    enc_dl = client.get(
        f"/api/models/{enc_id}",
        headers={"Authorization": f"Bearer {recipient_token}"},
    )
    assert enc_dl.status_code == 200

    # Recipient decrypts; decrypted bytes are mock_decrypted in stub mode
    dec = client.post(
        "/api/models/decrypt",
        headers={"Authorization": f"Bearer {recipient_token}"},
        json={"model_id": enc_id},
    )
    assert dec.status_code == 200
    dec_id = int(dec.json()["decrypted_model_id"])
    dec_dl = client.get(
        f"/api/models/{dec_id}",
        headers={"Authorization": f"Bearer {recipient_token}"},
    )
    assert dec_dl.status_code == 200

    # Sign + verify by recipient
    sig = client.post(
        "/api/models/sign",
        headers={"Authorization": f"Bearer {recipient_token}"},
        json={"model_id": dec_id},
    )
    assert sig.status_code == 200
    signature_b64 = sig.json()["signature_b64"]

    ver = client.post(
        "/api/models/verify",
        headers={"Authorization": f"Bearer {recipient_token}"},
        json={"model_id": dec_id, "signature_b64": signature_b64, "signer_id": recipient},
    )
    assert ver.status_code == 200
    assert ver.json()["valid"] is True
