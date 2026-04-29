import { request } from './client'

// ─────────────────────────────────────────────────────────────────────
// Categories (entidad propia tras T6.3)
// ─────────────────────────────────────────────────────────────────────

export function getCategories() {
  return request('/categories')
}

export function createCategory(payload) {
  return request('/categories', { method: 'POST', body: payload })
}

export function updateCategory(id, payload) {
  return request(`/categories/${id}`, { method: 'PUT', body: payload })
}

export function deleteCategory(id) {
  return request(`/categories/${id}`, { method: 'DELETE' })
}

// ─────────────────────────────────────────────────────────────────────
// Information Sources (medios)
// ─────────────────────────────────────────────────────────────────────

export function getInformationSources() {
  return request('/information-sources')
}

export function createInformationSource(payload) {
  return request('/information-sources', { method: 'POST', body: payload })
}

export function updateInformationSource(id, payload) {
  return request(`/information-sources/${id}`, { method: 'PUT', body: payload })
}

export function deleteInformationSource(id) {
  return request(`/information-sources/${id}`, { method: 'DELETE' })
}

export function getSourcesCatalogSummary() {
  return request('/information-sources/catalog/summary')
}

// ─────────────────────────────────────────────────────────────────────
// RSS Channels (anidados bajo information-sources)
// ─────────────────────────────────────────────────────────────────────

export function getRssChannelsForSource(sourceId) {
  return request(`/information-sources/${sourceId}/rss-channels`)
}

export async function getAllRssChannels() {
  const sources = await getInformationSources()
  const allChannels = []
  for (const source of sources) {
    const channels = await getRssChannelsForSource(source.id)
    for (const channel of channels) {
      allChannels.push({ ...channel, _medium: source })
    }
  }
  return allChannels
}

export function createRssChannel(sourceId, payload) {
  return request(`/information-sources/${sourceId}/rss-channels`, {
    method: 'POST',
    body: payload,
  })
}

export function updateRssChannel(sourceId, channelId, payload) {
  return request(`/information-sources/${sourceId}/rss-channels/${channelId}`, {
    method: 'PUT',
    body: payload,
  })
}

export function deleteRssChannel(sourceId, channelId) {
  return request(`/information-sources/${sourceId}/rss-channels/${channelId}`, {
    method: 'DELETE',
  })
}

export function activateRssChannel(sourceId, channelId) {
  return request(`/information-sources/${sourceId}/rss-channels/${channelId}/activate`, {
    method: 'PATCH',
  })
}

export function deactivateRssChannel(sourceId, channelId) {
  return request(`/information-sources/${sourceId}/rss-channels/${channelId}/deactivate`, {
    method: 'PATCH',
  })
}

// ─────────────────────────────────────────────────────────────────────
// Compat: shim que devuelve canales con shape parecido al antiguo Source
// para minimizar cambios en otras páginas que aún consumen "sources".
// ─────────────────────────────────────────────────────────────────────

export async function getSources() {
  const channels = await getAllRssChannels()
  return channels.map((channel) => ({
    id: channel.id,
    medium_name: channel._medium?.name || '',
    medium_id: channel._medium?.id,
    name: channel._medium?.name || '',
    url: channel.url,
    category_id: channel.category_id,
    is_active: channel.is_active,
    information_source_id: channel.information_source_id,
  }))
}
