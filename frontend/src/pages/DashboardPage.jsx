import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getHealth } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { getAlerts, getAlertsStats } from '../api/alertsApi'
import {
  getMyNewsStats,
  getMyNewsWordcloud,
  getNews,
} from '../api/newsApi'
import { getNotifications } from '../api/notificationsApi'

const CHART_COLORS = [
  '#17324d', '#bb4d00', '#2a5478', '#d4742e', '#3d6f9e',
  '#586579', '#8c5a2a', '#4a8ac2', '#a06030', '#6b8faa',
  '#7a4a14', '#3b5068', '#c98040', '#28425a', '#9e6838',
  '#506a80', '#d09050',
]

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
      gap: '0.5rem 0.8rem',
      justifyContent: 'center',
      alignItems: 'baseline',
      padding: '1rem 0.5rem',
    }}>
      {words.map((word, i) => {
        const ratio = maxValue === minValue ? 0.5 : (word.value - minValue) / (maxValue - minValue)
        const fontSize = 0.75 + ratio * 1.6
        const color = CHART_COLORS[i % CHART_COLORS.length]
        return (
          <span
            key={word.text}
            title={`${word.text}: ${word.value}`}
            style={{
              fontSize: `${fontSize}rem`,
              fontWeight: ratio > 0.5 ? 700 : 400,
              color,
              opacity: 0.5 + ratio * 0.5,
              cursor: 'default',
              lineHeight: 1.3,
              textTransform: ratio > 0.7 ? 'uppercase' : 'none',
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
          getMyNewsStats(),
          getAlertsStats(),
          getMyNewsWordcloud(),
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
        const data = await getMyNewsWordcloud({ category: wordcloudCategory || undefined })
        if (!ignore) setWordcloudData(data)
      } catch { /* ignore */ }
    }
    reload()
    return () => { ignore = true }
  }, [wordcloudCategory])

  const newsByCategory = newsStats?.by_category || []
  const alertsByCategory = alertsStats?.by_category || []
  const availableCategories = newsByCategory.map((c) => c.category)

  const userName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || t('dashboard.unknown_user')

  return (
    <section className="dashboard-page">
      {/* ── Row 1: Stat cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        <article className="panel-card" style={{ textAlign: 'center' }}>
          <p className="eyebrow" style={{ marginBottom: '0.5rem' }}>{t('dashboard.total_news')}</p>
          <p style={{ fontSize: '2.2rem', fontWeight: 700, margin: 0 }}>
            {newsStats === null ? '...' : newsStats.total_news.toLocaleString()}
          </p>
          <p className="panel-card__text" style={{ fontSize: '0.8rem' }}>{t('dashboard.total_news_label')}</p>
        </article>

        <article className="panel-card" style={{ textAlign: 'center' }}>
          <p className="eyebrow" style={{ marginBottom: '0.5rem' }}>{t('dashboard.active_alerts')}</p>
          <p style={{ fontSize: '2.2rem', fontWeight: 700, margin: 0 }}>
            {activeAlertsCount === null ? '...' : activeAlertsCount}
          </p>
          <p className="panel-card__text" style={{ fontSize: '0.8rem' }}>{t('dashboard.alerts_active')}</p>
        </article>

        <article className="panel-card" style={{ textAlign: 'center' }}>
          <p className="eyebrow" style={{ marginBottom: '0.5rem' }}>{t('dashboard.unread_notifications')}</p>
          <p style={{ fontSize: '2.2rem', fontWeight: 700, margin: 0 }}>
            {unreadCount === null ? '...' : unreadCount}
          </p>
          <p className="panel-card__text" style={{ fontSize: '0.8rem' }}>{t('dashboard.notifications_pending')}</p>
        </article>

        <article className="panel-card" style={{ textAlign: 'center' }}>
          <p className="eyebrow" style={{ marginBottom: '0.5rem' }}>{t('dashboard.backend_status')}</p>
          {health.status === 'loading' ? <p>...</p> : null}
          {health.status === 'success' ? (
            <span className="status-pill status-pill--ok" style={{ margin: '0 auto' }}>{t('dashboard.backend_reachable')}</span>
          ) : null}
          {health.status === 'error' ? (
            <span className="status-pill status-pill--error" style={{ margin: '0 auto' }}>{t('dashboard.connection_issue')}</span>
          ) : null}
        </article>
      </div>

      {/* ── Row 2: Charts side by side (horizontal bars) ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <article className="panel-card">
          <h2>{t('dashboard.news_by_category')}</h2>
          {newsByCategory.length === 0 ? (
            <p className="panel-card__text">{t('dashboard.no_data')}</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={Math.max(200, newsByCategory.length * 40)}>
                <BarChart data={newsByCategory} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="category" width={100} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" name={t('dashboard.news_count')} radius={[0, 6, 6, 0]}>
                    {newsByCategory.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {newsByCategory.map((item, i) => (
                  <div key={item.category} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <span style={{ color: 'var(--muted)' }}>{item.category}</span>
                    <span style={{ fontWeight: 700 }}>{item.count}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </article>

        <article className="panel-card">
          <h2>{t('dashboard.alerts_by_category')}</h2>
          {alertsByCategory.length === 0 ? (
            <p className="panel-card__text">{t('dashboard.no_data')}</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={Math.max(200, alertsByCategory.length * 40)}>
                <BarChart data={alertsByCategory} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="category" width={100} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" name={t('dashboard.alerts_count')} radius={[0, 6, 6, 0]}>
                    {alertsByCategory.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {alertsByCategory.map((item) => (
                  <div key={item.category} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <span style={{ color: 'var(--muted)' }}>{item.category}</span>
                    <span style={{ fontWeight: 700 }}>{item.count}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </article>
      </div>

      {/* ── Row 3: Word cloud + Latest news side by side ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <article className="panel-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <h2 style={{ margin: 0 }}>{t('dashboard.wordcloud')}</h2>
            <select
              value={wordcloudCategory}
              onChange={(e) => setWordcloudCategory(e.target.value)}
              style={{
                padding: '0.35rem 0.7rem',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--bg)',
                fontSize: '0.8rem',
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

        <article className="panel-card">
          <h2>{t('dashboard.latest_news')}</h2>
          {latestNews.length === 0 ? (
            <p className="panel-card__text">{t('dashboard.no_news')}</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {latestNews.map((item) => (
                <li key={item.id} style={{ fontSize: '0.88rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
                  <strong>{item.title}</strong>
                  {item.published_at ? (
                    <span style={{ display: 'block', color: 'var(--muted)', fontSize: '0.78rem', marginTop: '0.15rem' }}>
                      {new Date(item.published_at).toLocaleString()}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>

      {/* ── Row 4: User info compact ── */}
      <article className="panel-card" style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0 }}>{t('dashboard.current_user')}</h2>
        <dl style={{ display: 'flex', gap: '2rem', margin: 0, flexWrap: 'wrap' }}>
          <div>
            <dt style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>{t('dashboard.name')}</dt>
            <dd style={{ margin: 0, fontWeight: 700 }}>{userName}</dd>
          </div>
          <div>
            <dt style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>{t('dashboard.email')}</dt>
            <dd style={{ margin: 0, fontWeight: 700 }}>{user?.email || t('dashboard.not_available')}</dd>
          </div>
          <div>
            <dt style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>{t('dashboard.role')}</dt>
            <dd style={{ margin: 0, fontWeight: 700 }}>{user?.role || 'reader'}</dd>
          </div>
          <div>
            <dt style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>{t('dashboard.organization')}</dt>
            <dd style={{ margin: 0, fontWeight: 700 }}>{user?.organization || t('dashboard.not_assigned')}</dd>
          </div>
        </dl>
      </article>
    </section>
  )
}
