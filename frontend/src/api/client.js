const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const TOKEN_STORAGE_KEY = 'newsradar.access_token'

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

function buildUrl(path) {
  return `${API_BASE_URL}${path}`
}

function extractErrorMessage(payload, fallback) {
  if (!payload) {
    return fallback
  }

  if (typeof payload === 'string') {
    return payload
  }

  if (typeof payload.detail === 'string') {
    return payload.detail
  }

  if (typeof payload.message === 'string') {
    return payload.message
  }

  return fallback
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  const text = await response.text()
  return text || null
}

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY)
}

export async function request(
  path,
  { method = 'GET', body, headers = {}, token } = {},
) {
  const resolvedToken = token || getStoredToken()
  const requestHeaders = {
    Accept: 'application/json',
    ...headers,
  }

  if (body && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  if (resolvedToken) {
    requestHeaders.Authorization = `Bearer ${resolvedToken}`
  }

  const response = await fetch(buildUrl(path), {
    method,
    headers: requestHeaders,
    body: body && !(body instanceof FormData) ? JSON.stringify(body) : body,
  })

  const payload = await parseResponse(response)

  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(payload, `Request failed with status ${response.status}.`),
      response.status,
      payload,
    )
  }

  return payload
}

export function getHealth() {
  return request('/health')
}
