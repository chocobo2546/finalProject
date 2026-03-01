const DEFAULT_BASE = 'http://localhost:8000'

export function getBackendBase() {
  return (import.meta.env.VITE_BACKEND_URL || DEFAULT_BASE).replace(/\/$/, '')
}

export async function apiGet(path) {
  const res = await fetch(`${getBackendBase()}${path}`)
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

export async function apiPost(path, body) {
  const res = await fetch(`${getBackendBase()}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

export async function apiDelete(path) {
  const res = await fetch(`${getBackendBase()}${path}`, { method: 'DELETE' })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

export function openSSE(path) {
  return new EventSource(`${getBackendBase()}${path}`)
}
