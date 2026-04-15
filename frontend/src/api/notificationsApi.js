import { request } from './client'

export function getNotifications() {
  return request('/notifications/')
}

export function markAsRead(id) {
  return request(`/notifications/${id}/read`, { method: 'PATCH' })
}

export function markAsUnread(id) {
  return request(`/notifications/${id}/unread`, { method: 'PATCH' })
}

export function deleteNotification(id) {
  return request(`/notifications/${id}`, { method: 'DELETE' })
}
