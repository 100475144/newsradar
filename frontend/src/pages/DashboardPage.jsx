import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getHealth } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { getAlerts, getAlertsStats } from '../api/alertsApi'
import { getNews, getNewsStats, getNewsWordcloud } from '../api/newsApi'
import { getNotifications } from '../api/notificationsApi'

const CHART_COLORS = [
  '#6366f1', '#8b5cf6', '#a78bfa', '#c084fc', '#e879f9',
  '#f472b6', '#fb7185', '#f87171', '#fb923c', '#fbbf24',
  '#a3e635', '#34d399', '#2dd4bf', '#22d3ee', '#38bdf8',
  '#60a5fa', '#818cf8',
]

function formatTimestamp(value, t) {
  if (!value) return t('dashboard.not_available')
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function WordCloud({ words, t }) {
  if (!words || words.length === 0) {
    return <p className="panel-card__text">{t('dashboard.no_wordcloud_data')}</p>
  }

  const maxValue = Math.max(...words.map((w) => w.value))
  const minValue = Math.min(...words.map((w) => w.value))

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.4rem',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '0.5rem',
    }}>
      {words.map((word, i) => {
        const ratio = maxValue === minValue ? 0.5 : (word.value - minValue) / (maxValue - minValue)
        const fontSize = 0.7 + ratio * 1.8
        const opacity = 0.45 + ratio * 0.55
        const color = CHART_COLORS[i % CHART_COLORS.length]
        return (
          <span
            key={word.text}
            title={`${word.text}: ${word.value}`}
            style={{
              fontSize: `${fontSize}rem`,
              fontWeight: ratio > 0.5 ? 700 : 400,
              color,
              opacity,
              cursor: 'default',
              lineHeight: 1.2,
            }}
          >
            {word.text}
          </span>
        )
      })}
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { t } = useTranslation()
  const [health, setHealth] = useState({ status: 'loading', data: null, error: '' })
  const [activeAlertsCount, setActiveAlertsCount] = useState(null)
  const [latestNews, setLatestNews] = useState([])
  const [unreadCount, setUnreadCount] = useState(null)
  const [newsStats, setNewsStats] = useState(null)
  const [alertsStats, setAlertsStats] = useState(null)
  const [wordcloudData, setWordcloudData] = useState(null)
  const [wordcloudCategory, setWordcloudCategory] = useState('')

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
        const [alerts, news, notifications, nStats, aStats, wcloud] = await Promise.all([
          getAlerts(),
          getNews({ limit: 5 }),
          getNotifications(),
          getNewsStats(),
          getAlertsStats(),
          getNewsWordcloud(),
        ])
        if (!ignore) {
          setActiveAlertsCount(alerts.filter((a) => a.is_active).length)
          setLatestNews(news.items ? news.items.slice(0, 5) : news.slice(0, 5))
          setUnreadCount(notifications.filter((n) => !n.is_read).length)
          setNewsStats(nStats)
          setAlertsStats(aStats)
          setWordcloudData(wcloud)
        }
      } catch {
        // widgets are non-critical, fail silently
      }
    }

    loadWidgets()
    return () => { ignore = true }
  }, [])

  useEffect(() => {
    let ignore = false
    async function reload() {
      try {
        const data = await getNewsWordcloud({ category: wordcloudCategory || undefined })
        if (!ignore) setWordcloudData(data)
      } catch { /* ignore */ }
    }
    reload()
    return () => { ignore = true }
  }, [wordcloudCategory])

  const newsByCategory = newsStats?.by_category || []
  const alertsByCategory = alertsStats?.by_category || []
  const availableCategories = newsByCategory.map((c) => c.category)

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
          <h2>{t('dashboard.total_news')}</h2>
          {newsStats === null ? (
            <p className="panel-card__text">{t('dashboard.loading')}</p>
          ) : (
            <p style={{ fontSize: '2.5rem', fontWeight: 700, margin: 0 }}>{newsStats.total_news}</p>
          )}
          <p className="panel-card__text">{t('dashboard.total_news_label')}</p>
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
          <h2>{t('dashboard.unread_notifications')}</h2>
          {unreadCount === null ? (
            <p className="panel-card__text">{t('dashboard.loading')}</p>
          ) : (
            <p style={{ fontSize: '2.5rem', fontWeight: 700, margin: 0 }}>{unreadCount}</p>
          )}
          <p className="panel-card__text">{t('dashboard.notifications_pending')}</p>
        </article>

        <article className="panel-card" style={{ gridColumn: '1 / -1' }}>
          <h2>{t('dashboard.news_by_category')}</h2>
          {newsByCategory.length === 0 ? (
            <p className="panel-card__text">{t('dashboard.no_data')}</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={newsByCategory} margin={{ top: 5, right: 20, bottom: 60, left: 0 }}>
                <XAxis
                  dataKey="category"
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                  tick={{ fontSize: 11 }}
                  height={80}
                />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" name={t('dashboard.news_count')} radius={[6, 6, 0, 0]}>
                  {newsByCategory.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </article>

        <article className="panel-card" style={{ gridColumn: '1 / -1' }}>
          <h2>{t('dashboard.alerts_by_category')}</h2>
          {alertsByCategory.length === 0 ? (
            <p className="panel-card__text">{t('dashboard.no_data')}</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={alertsByCategory} margin={{ top: 5, right: 20, bottom: 60, left: 0 }}>
                <XAxis
                  dataKey="category"
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                  tick={{ fontSize: 11 }}
                  height={80}
                />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" name={t('dashboard.alerts_count')} radius={[6, 6, 0, 0]}>
                  {alertsByCategory.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </article>

        <article className="panel-card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0 }}>{t('dashboard.wordcloud')}</h2>
            <select
              value={wordcloudCategory}
              onChange={(e) => setWordcloudCategory(e.target.value)}
              style={{
                padding: '0.4rem 0.8rem',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--bg)',
                fontSize: '0.85rem',
              }}
            >
              <option value="">{t('dashboard.all_categories')}</option>
              {availableCategories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <WordCloud words={wordcloudData} t={t} />
        </article>

        <article className="panel-card" style={{ gridColumn: '1 / -1' }}>
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
      </div>
    </section>
  )
}
