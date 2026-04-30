async function request(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (body?.detail) {
        message = body.detail
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message)
  }
  return response.json()
}

const API_BASE = '/api'

export function getTargets(params = {}) {
  const url = new URL(`${API_BASE}/targets`, window.location.origin)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })
  return request(url.toString(), { method: 'GET' })
}

export function getMe() {
  return request(`${API_BASE}/auth/me`, { method: 'GET' })
}

export function getLocation() {
  return request(`${API_BASE}/auth/location`, { method: 'GET' })
}

async function requestText(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'include',
    ...options,
  })
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`
    try {
      const body = await response.json()
      if (body?.detail) {
        message = body.detail
      }
    } catch {
      const text = await response.text()
      if (text) {
        message = text
      }
    }
    throw new Error(message)
  }
  return response.text()
}

export function getCharacterProfile() {
  return request(`${API_BASE}/character/profile`, { method: 'GET' })
}

export function getCharacterSkillExport() {
  return requestText(`${API_BASE}/character/skills/export`, { method: 'GET' })
}

export function getSkillExport() {
  return getCharacterSkillExport()
}

export function getCurrentShipFit() {
  return request(`${API_BASE}/character/current-ship/fit`, { method: 'GET' })
}

export function postLogout() {
  return request(`${API_BASE}/auth/logout`, { method: 'POST' })
}
