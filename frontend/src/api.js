/** API client for QModelGuard backend.
 * Uses relative paths; Vite proxy maps /api and /health to backend.
 * No hardcoded localhost unless VITE_API_PROXY_TARGET env overrides.
 */
const API_BASE = '/api'

async function readJson(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // backend errors look like: { detail: "..." }
    throw new Error(data?.detail || `Request failed: ${res.status}`);
  }
  return data;
}

export async function checkHealth() {
  const res = await fetch("/health");
  const data = await readJson(res);
  if (data?.status !== "ok") throw new Error("Invalid health response");
  return data;
}
function authHeaders(token) {
  return token ? { Authorization: "Bearer " + token } : {};
}

export async function generateKeys(token) {
  const res = await fetch(`${API_BASE}/keys/generate`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return readJson(res);
}

export async function getPublicKeys(token) {
  const res = await fetch(`${API_BASE}/keys/public`, {
    headers: authHeaders(token),
  });
  return readJson(res);
}

export async function getPublicKeyById(id) {
  const res = await fetch(`${API_BASE}/keys/public/${id}`);
  return readJson(res);
}

export async function uploadModel(file, token) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API_BASE}/models/upload`, {
    method: "POST",
    headers: authHeaders(token),
    body: fd,
  });
  return readJson(res);
}

/** GET /api/models/{id} - returns blob */
export async function getModel(id, token) {
  const res = await fetch(`${API_BASE}/models/${id}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail || `Request failed: ${res.status}`);
  }
  return res.blob();
}

/** POST /api/models/encrypt - FormData: model (file), recipient (user id/name) */
export async function encryptModel(token, formData) {
  const res = await fetch(`${API_BASE}/models/encrypt`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return readJson(res);
}

/** POST /api/models/decrypt - FormData: model (file) */
export async function decryptModel(token, formData) {
  const res = await fetch(`${API_BASE}/models/decrypt`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return readJson(res);
}

/** POST /api/models/sign - FormData: model (file) */
export async function signModel(token, formData) {
  const res = await fetch(`${API_BASE}/models/sign`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return readJson(res);
}

/** POST /api/models/verify - FormData: model (file), signature (file), signer (id/name) */
export async function verifyModel(token, formData) {
  const res = await fetch(`${API_BASE}/models/verify`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return readJson(res);
}

export async function register(username, password) {
  const res = await fetch(`${API_BASE}/users/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return readJson(res); // returns { token, user_id } OR throws Error(detail)
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/users/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return readJson(res); // returns { token, user_id } OR throws Error(detail)
}

export async function getMe(token) {
  const res = await fetch(`${API_BASE}/users/me`, {
    headers: { Authorization: "Bearer " + token },
  });
  return readJson(res); // returns { user_id, username } OR throws Error(detail)
}