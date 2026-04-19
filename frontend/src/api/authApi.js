import { request } from './client'

export function registerUser(payload) {
  return request('/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function verifyEmail(token) {
  return request(`/auth/verify-email?token=${encodeURIComponent(token)}`)
}

export function resendVerification(email) {
  return request(`/auth/resend-verification?email=${encodeURIComponent(email)}`, {
    method: 'POST',
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
