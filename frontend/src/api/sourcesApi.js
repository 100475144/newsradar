import { request } from './client'

export function getSources() {
  return request('/sources')
}

export function getSourcesCatalogSummary() {
  return request('/sources/catalog/summary')
}

export function createSource(payload) {
  return request('/sources', {
    method: 'POST',
    body: payload,
  })
}

export function updateSource(id, payload) {
  return request(`/sources/${id}`, {
    method: 'PUT',
    body: payload,
  })
}

export function deleteSource(id) {
  return request(`/sources/${id}`, {
    method: 'DELETE',
  })
}
