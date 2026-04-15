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
