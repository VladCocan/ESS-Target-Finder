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
    throw new Error(`${response.status} ${response.statusText}`)
  }
  return response.json()
}

export function getTargets(params = {}) {
  const url = new URL('/targets', window.location.origin)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })
  return request(url.toString(), { method: 'GET' })
}

export function getMe() {
  return request('/api/auth/me', { method: 'GET' })
}

export function getLocation() {
  return request('/api/auth/location', { method: 'GET' })
}

export function postLogout() {
  return request('/api/auth/logout', { method: 'POST' })
}
