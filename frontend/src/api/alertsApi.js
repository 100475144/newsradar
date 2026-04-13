import { request } from './client'

export function getAlerts() {
  return request('/alerts')
}

export function createAlert(payload) {
  return request('/alerts', {
    method: 'POST',
    body: payload,
  })
}

export function getAlert(id) {
  return request(`/alerts/${id}`)
}

export function updateAlert(id, payload) {
  return request(`/alerts/${id}`, {
    method: 'PUT',
    body: payload,
  })
}

export function deleteAlert(id) {
  return request(`/alerts/${id}`, {
    method: 'DELETE',
  })
}

export function activateAlert(id) {
  return request(`/alerts/${id}/activate`, {
    method: 'PATCH',
  })
}

export function deactivateAlert(id) {
  return request(`/alerts/${id}/deactivate`, {
    method: 'PATCH',
  })
}

export function getAlertSuggestions(keyword) {
  return request(`/alerts/suggestions/${encodeURIComponent(keyword)}`)
}
