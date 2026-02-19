/** API client for QModelGuard backend.
 * Uses relative paths; Vite proxy maps /api and /health to backend.
 * No hardcoded localhost unless VITE_API_PROXY_TARGET env overrides.
 */
const API_BASE = '/api'

/** Check backend connectivity. Returns { ok: true } or throws. */
export async function checkHealth() {
  const res = await fetch('/health')
  if (!res.ok) throw new Error(`Backend error: ${res.status}`)
  const data = await res.json()
  if (data?.status !== 'ok') throw new Error('Invalid health response')
  return data
}

export async function generateKeys() {
  const res = await fetch(`${API_BASE}/keys/generate`, { method: 'POST' })
  return res.json()
}

export async function getPublicKeys() {
  const res = await fetch(`${API_BASE}/keys/public`)
  return res.json()
}

export async function getPublicKeyById(id) {
  const res = await fetch(`${API_BASE}/keys/public/${id}`)
  return res.json()
}

export async function uploadModel(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${API_BASE}/models/upload`, {
    method: 'POST',
    body: fd,
  })
  return res.json()
}

export async function register(username, password) {
  const res = await fetch(`${API_BASE}/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  return res.json()
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  return res.json()
}
