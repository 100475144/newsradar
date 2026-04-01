import { request } from './client'

export function registerUser(payload) {
  return request('/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function loginUser(payload) {
  return request('/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function getCurrentUser(token) {
  return request('/auth/me', {
    token,
  })
}
