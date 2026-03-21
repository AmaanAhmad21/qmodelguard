/** API client for QModelGuard backend.
 * Uses relative paths; Vite proxy maps /api and /health to backend.
 * No hardcoded localhost unless VITE_API_PROXY_TARGET env overrides.
 */

const API_BASE = '/api';

/** Error with status for handling 401 (session expired) etc. */
export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Turn FastAPI error body into a single message string. */
function parseApiErrorDetail(body) {
  if (!body || typeof body !== 'object') return null;
  const d = body.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && d.length > 0) {
    return d.map((x) => (x.msg != null ? `${x.loc?.slice(-1)?.[0] ?? 'field'}: ${x.msg}` : String(x))).join('. ');
  }
  return null;
}

async function readJson(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = parseApiErrorDetail(data) || `Request failed (${res.status})`;
    throw new ApiError(message, res.status);
  }
  return data;
}

/** Wrapper: run fetch; catch network errors and throw ApiError. */
async function apiFetch(url, options = {}) {
  try {
    return await fetch(url, options);
  } catch (e) {
    if (e instanceof ApiError) throw e;
    const msg = (e?.message && (e.message.includes('fetch') || e.message.includes('Failed to fetch')))
      ? 'Network error. Is the backend running?'
      : (e?.message || 'Request failed');
    throw new ApiError(msg, 0);
  }
}

export async function checkHealth() {
  const res = await apiFetch("/health");
  const data = await readJson(res);
  if (data?.status !== "ok") throw new ApiError("Invalid health response");
  return data;
}
function authHeaders(token) {
  return token ? { Authorization: "Bearer " + token } : {};
}

export async function generateKeys(token) {
  const res = await apiFetch(`${API_BASE}/keys/generate`, {
    method: "POST",
    headers: authHeaders(token),
  });
  return readJson(res);
}

export async function getPublicKeys(token) {
  const res = await apiFetch(`${API_BASE}/keys/public`, {
    headers: authHeaders(token),
  });
  return readJson(res);
}

export async function getPublicKeyById(id) {
  const res = await apiFetch(`${API_BASE}/keys/public/${id}`);
  return readJson(res);
}

export async function listUsers(token) {
  const res = await apiFetch(`${API_BASE}/users/list`, {
    headers: authHeaders(token),
  });
  return readJson(res);
}

export async function uploadModel(file, token) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await apiFetch(`${API_BASE}/models/upload`, {
    method: "POST",
    headers: authHeaders(token),
    body: fd,
  });
  return readJson(res);
}

/** GET /api/models - list current user's models (paginated) */
export async function listModels(token, limit = 50, offset = 0) {
  const res = await apiFetch(
    `${API_BASE}/models?limit=${limit}&offset=${offset}`,
    { headers: authHeaders(token) }
  );
  return readJson(res);
}

/** DELETE /api/models/{id} */
export async function deleteModel(id, token) {
  const res = await apiFetch(`${API_BASE}/models/${id}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  return readJson(res);
}

/** GET /api/models/{id} - returns blob */
export async function getModel(id, token) {
  const res = await apiFetch(`${API_BASE}/models/${id}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const message = parseApiErrorDetail(data) || `Request failed (${res.status})`;
    throw new ApiError(message, res.status);
  }
  return res.blob();
}

/** POST /api/models/encrypt - JSON: { model_id, recipient_id } */
export async function encryptModel(token, { model_id, recipient_id }) {
  const res = await apiFetch(`${API_BASE}/models/encrypt`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ model_id: Number(model_id), recipient_id }),
  });
  return readJson(res);
}

/** POST /api/models/decrypt - JSON: { model_id } */
export async function decryptModel(token, { model_id }) {
  const res = await apiFetch(`${API_BASE}/models/decrypt`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ model_id: Number(model_id) }),
  });
  return readJson(res);
}

/** POST /api/models/sign - JSON: { model_id }; returns { signature_b64 } */
export async function signModel(token, { model_id }) {
  const res = await apiFetch(`${API_BASE}/models/sign`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ model_id: Number(model_id) }),
  });
  return readJson(res);
}

/** POST /api/models/verify - JSON: { model_id, signature_b64, signer_id }; returns { valid } */
export async function verifyModel(token, { model_id, signature_b64, signer_id }) {
  const res = await apiFetch(`${API_BASE}/models/verify`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({
      model_id: Number(model_id),
      signature_b64,
      signer_id,
    }),
  });
  return readJson(res);
}

export async function register(username, password) {
  const res = await apiFetch(`${API_BASE}/users/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return readJson(res);
}

export async function login(username, password) {
  const res = await apiFetch(`${API_BASE}/users/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return readJson(res);
}

export async function getMe(token) {
  const res = await apiFetch(`${API_BASE}/users/me`, {
    headers: { Authorization: "Bearer " + token },
  });
  return readJson(res);
}

/** GET /api/activity - recent activity for current user */
export async function listActivity(token, limit = 20) {
  const res = await apiFetch(`${API_BASE}/activity?limit=${limit}`, {
    headers: authHeaders(token),
  });
  return readJson(res);
}