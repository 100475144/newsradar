import { request } from './client'

// Endpoints anidados oficiales: /users/me/alerts (atajo del backend).
// Para edición/borrado el backend usa /users/{user_id}/alerts/{id}; el
// frontend resuelve user_id desde la respuesta de cada alerta.

export function getAlerts() {
  return request('/users/me/alerts')
}

export function createAlert(payload) {
  return request('/users/me/alerts', { method: 'POST', body: payload })
}

export function getAlert(userId, id) {
  return request(`/users/${userId}/alerts/${id}`)
}

export function updateAlert(userId, id, payload) {
  return request(`/users/${userId}/alerts/${id}`, { method: 'PUT', body: payload })
}

export function deleteAlert(userId, id) {
  return request(`/users/${userId}/alerts/${id}`, { method: 'DELETE' })
}

export function activateAlert(userId, id) {
  return request(`/users/${userId}/alerts/${id}/activate`, { method: 'PATCH' })
}

export function deactivateAlert(userId, id) {
  return request(`/users/${userId}/alerts/${id}/deactivate`, { method: 'PATCH' })
}

export function getAlertSuggestions(keyword) {
  return request(`/alerts/suggestions/${encodeURIComponent(keyword)}`)
}

export function getAlertsStats() {
  return request('/alerts/me/stats')
}
