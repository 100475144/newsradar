import { request } from './client'

export function getNews({ skip = 0, limit = 20, sourceId, category } = {}) {
  const params = new URLSearchParams()
  params.set('skip', skip)
  params.set('limit', limit)
  if (sourceId) params.set('source_id', sourceId)
  if (category) params.set('category', category)
  return request(`/news?${params.toString()}`)
}

export function getNewsById(id) {
  return request(`/news/${id}`)
}

export function getNewsStats() {
  return request('/news/stats')
}

export function getNewsWordcloud({ category, limit = 50 } = {}) {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  params.set('limit', limit)
  return request(`/news/wordcloud?${params.toString()}`)
}

// CAMBIO #2: dashboard/wordcloud per-user usando alertas del logueado.
export function getMyNewsStats() {
  return request('/news/me/stats')
}

export function getMyNewsWordcloud({ category, limit = 50 } = {}) {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  params.set('limit', limit)
  return request(`/news/me/wordcloud?${params.toString()}`)
}
