import React, { useCallback, useEffect, useReducer, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  deleteNotification,
  getNotifications,
  markAsRead,
  markAsUnread,
} from '../api/notificationsApi'

function notificationsReducer(state, action) {
  switch (action.type) {
    case 'LOADING':
      return { ...state, status: 'loading', error: '' }
    case 'LOADED':
      return { status: 'success', items: action.items, error: '' }
    case 'ERROR':
      return { ...state, status: 'error', error: action.error }
    case 'UPDATE':
      return {
        ...state,
        items: state.items.map((n) => (n.id === action.item.id ? action.item : n)),
      }
    case 'REMOVE':
      return { ...state, items: state.items.filter((n) => n.id !== action.id) }
    default:
      return state
  }
}

function NotificationRow({ notification, onToggleRead, onDelete, busy }) {
  const { t } = useTranslation()

  return (
    <div
      className="source-row"
      style={{
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: '0.5rem',
        opacity: notification.is_read ? 0.65 : 1,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%' }}>
        <strong className="source-row__name" style={{ flex: 1 }}>
          {notification.title}
        </strong>
        <span
          className={
            notification.is_read
              ? 'source-badge source-badge--inactive'
              : 'source-badge source-badge--active'
          }
        >
          {notification.is_read ? t('notifications.read') : t('notifications.unread')}
        </span>
      </div>

      <pre style={{
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        fontSize: '0.88rem',
        background: 'rgba(16,32,51,0.04)',
        color: 'var(--text)',
        borderRadius: '12px',
        padding: '0.75rem',
        margin: 0,
        width: '100%',
      }}>
        {notification.message}
      </pre>

      <div className="source-row__actions">
        <button
          type="button"
          className="secondary-button"
          onClick={() => onToggleRead(notification)}
          disabled={busy}
        >
          {notification.is_read ? t('notifications.mark_unread') : t('notifications.mark_read')}
        </button>
        <button
          type="button"
          className="danger-button"
          onClick={() => onDelete(notification.id)}
          disabled={busy}
        >
          {t('notifications.delete')}
        </button>
      </div>
    </div>
  )
}

export default function NotificationsPage() {
  const { t } = useTranslation()
  const [state, dispatch] = useReducer(notificationsReducer, {
    status: 'loading',
    items: [],
    error: '',
  })
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const items = await getNotifications()
      dispatch({ type: 'LOADED', items })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleToggleRead = async (notification) => {
    setBusyId(notification.id)
    try {
      const updated = notification.is_read
        ? await markAsUnread(notification.id)
        : await markAsRead(notification.id)
      dispatch({ type: 'UPDATE', item: updated })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    } finally {
      setBusyId(null)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('notifications.delete_confirm'))) return
    setBusyId(id)
    try {
      await deleteNotification(id)
      dispatch({ type: 'REMOVE', id })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    } finally {
      setBusyId(null)
    }
  }

  const unreadCount = state.items.filter((n) => !n.is_read).length

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">{t('notifications.eyebrow')}</p>
        <h1>{t('notifications.title')}</h1>
        <p>
          {t('notifications.subtitle')}{' '}
          {unreadCount > 0
            ? t('notifications.unread_count', { count: unreadCount })
            : t('notifications.all_caught_up')}
        </p>
      </div>

      {state.status === 'loading' ? (
        <p className="sources-feedback">{t('notifications.loading')}</p>
      ) : null}

      {state.status === 'error' ? (
        <p className="form-message form-message--error">{state.error}</p>
      ) : null}

      {state.status === 'success' && state.items.length === 0 ? (
        <div className="panel-card sources-empty">
          <p>{t('notifications.empty')}</p>
        </div>
      ) : null}

      {state.status === 'success' && state.items.length > 0 ? (
        <div className="sources-list">
          {state.items.map((notification) => (
            <NotificationRow
              key={notification.id}
              notification={notification}
              onToggleRead={handleToggleRead}
              onDelete={handleDelete}
              busy={busyId === notification.id}
            />
          ))}
        </div>
      ) : null}
    </section>
  )
}
