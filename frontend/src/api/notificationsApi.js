import { request } from './client'

// Tras T6.5, los endpoints anidados oficiales viven bajo
// /users/{user_id}/alerts/{alert_id}/notifications. Para la bandeja de entrada
// del usuario logueado usamos endpoints añadidos bajo /users/me/notifications.

export function getNotifications() {
  return request('/users/me/notifications')
}

export function getNotificationDetails(id) {
  return request(`/users/me/notifications/${id}/details`)
}

export function markAsRead(id) {
  return request(`/users/me/notifications/${id}/read`, { method: 'PATCH' })
}

export function markAsUnread(id) {
  return request(`/users/me/notifications/${id}/unread`, { method: 'PATCH' })
}

export function deleteNotification(id) {
  return request(`/users/me/notifications/${id}`, { method: 'DELETE' })
}
