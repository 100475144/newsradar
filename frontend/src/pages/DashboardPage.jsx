import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getHealth } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { getAlerts } from '../api/alertsApi'
import { getNews } from '../api/newsApi'
import { getNotifications } from '../api/notificationsApi'

function formatTimestamp(value, t) {
  if (!value) return t('dashboard.not_available')
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { t } = useTranslation()
  const [health, setHealth] = useState({ status: 'loading', data: null, error: '' })
  const [activeAlertsCount, setActiveAlertsCount] = useState(null)
  const [latestNews, setLatestNews] = useState([])
  const [unreadCount, setUnreadCount] = useState(null)

  useEffect(() => {
    let ignore = false

    async function loadHealth() {
      try {
        const data = await getHealth()
        if (!ignore) setHealth({ status: 'success', data, error: '' })
      } catch (error) {
        if (!ignore) setHealth({ status: 'error', data: null, error: error.message })
      }
    }

    loadHealth()
    return () => { ignore = true }
  }, [])

  useEffect(() => {
    let ignore = false

    async function loadWidgets() {
      try {
        const [alerts, news, notifications] = await Promise.all([
          getAlerts(),
          getNews({ limit: 5 }),
          getNotifications(),
        ])
        if (!ignore) {
          setActiveAlertsCount(alerts.filter((a) => a.is_active).length)
          setLatestNews(news.slice(0, 5))
          setUnreadCount(notifications.filter((n) => !n.is_read).length)
        }
      } catch {
        // widgets are non-critical, fail silently
      }
    }

    loadWidgets()
    return () => { ignore = true }
  }, [])

  return (
    <section className="dashboard-page">
      <div className="hero-card">
        <p className="eyebrow">{t('dashboard.eyebrow')}</p>
        <h1>{t('dashboard.title')}</h1>
        <p>{t('dashboard.subtitle')}</p>
      </div>

      <div className="dashboard-grid">
        <article className="panel-card">
          <h2>{t('dashboard.current_user')}</h2>
          <dl className="detail-list">
            <div>
              <dt>{t('dashboard.name')}</dt>
              <dd>{[user?.first_name, user?.last_name].filter(Boolean).join(' ') || t('dashboard.unknown_user')}</dd>
            </div>
            <div>
              <dt>{t('dashboard.email')}</dt>
              <dd>{user?.email || t('dashboard.not_available')}</dd>
            </div>
            <div>
              <dt>{t('dashboard.role')}</dt>
              <dd>{user?.role || 'reader'}</dd>
            </div>
            <div>
              <dt>{t('dashboard.organization')}</dt>
              <dd>{user?.organization || t('dashboard.not_assigned')}</dd>
            </div>
            <div>
              <dt>{t('dashboard.created_at')}</dt>
              <dd>{formatTimestamp(user?.created_at, t)}</dd>
            </div>
          </dl>
        </article>

        <article className="panel-card">
          <h2>{t('dashboard.backend_status')}</h2>
          {health.status === 'loading' ? <p>{t('dashboard.checking_api')}</p> : null}
          {health.status === 'success' ? (
            <div className="status-stack">
              <span className="status-pill status-pill--ok">{t('dashboard.backend_reachable')}</span>
              <pre>{JSON.stringify(health.data, null, 2)}</pre>
            </div>
          ) : null}
          {health.status === 'error' ? (
            <div className="status-stack">
              <span className="status-pill status-pill--error">{t('dashboard.connection_issue')}</span>
              <p>{health.error}</p>
            </div>
          ) : null}
        </article>

        <article className="panel-card">
          <h2>{t('dashboard.active_alerts')}</h2>
          {activeAlertsCount === null ? (
            <p className="panel-card__text">{t('dashboard.loading')}</p>
          ) : (
            <p style={{ fontSize: '2.5rem', fontWeight: 700, margin: 0 }}>{activeAlertsCount}</p>
          )}
          <p className="panel-card__text">{t('dashboard.alerts_active')}</p>
        </article>

        <article className="panel-card">
          <h2>{t('dashboard.latest_news')}</h2>
          {latestNews.length === 0 ? (
            <p className="panel-card__text">{t('dashboard.no_news')}</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {latestNews.map((item) => (
                <li key={item.id} style={{ fontSize: '0.88rem', borderBottom: '1px solid rgba(0,0,0,0.07)', paddingBottom: '0.4rem' }}>
                  <strong>{item.title}</strong>
                  {item.published_at ? (
                    <span style={{ display: 'block', color: 'rgba(0,0,0,0.45)', fontSize: '0.78rem' }}>
                      {new Date(item.published_at).toLocaleString()}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="panel-card">
          <h2>{t('dashboard.unread_notifications')}</h2>
          {unreadCount === null ? (
            <p className="panel-card__text">{t('dashboard.loading')}</p>
          ) : (
            <p style={{ fontSize: '2.5rem', fontWeight: 700, margin: 0 }}>{unreadCount}</p>
          )}
          <p className="panel-card__text">{t('dashboard.notifications_pending')}</p>
        </article>
      </div>
    </section>
  )
}
