import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getHealth } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { getAlerts } from '../api/alertsApi'
import { getMyNewsStats, getMyNewsWordcloud, getNews } from '../api/newsApi'
import { getNotifications } from '../api/notificationsApi'
import { getGlobalStats } from '../api/statsApi'

const CHART_COLORS = [
  '#17324d', '#bb4d00', '#2a5478', '#d4742e', '#3d6f9e',
  '#586579', '#8c5a2a', '#4a8ac2', '#a06030', '#6b8faa',
  '#7a4a14', '#3b5068', '#c98040', '#28425a', '#9e6838',
  '#506a80', '#d09050',
]

function formatNumber(value) {
  return value === null || value === undefined ? '...' : value.toLocaleString()
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

function StatCard({ eyebrow, value, label, accent }) {
  return (
    <article
      className="panel-card"
      style={{
        textAlign: 'left',
        borderTop: `4px solid ${accent}`,
        minHeight: '132px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <p className="eyebrow" style={{ marginBottom: '0.75rem', color: accent }}>{eyebrow}</p>
      <p style={{ fontSize: '2.25rem', fontWeight: 700, margin: 0, color: accent }}>
        {formatNumber(value)}
      </p>
      <p className="panel-card__text" style={{ fontSize: '0.82rem', marginBottom: 0 }}>{label}</p>
    </article>
  )
}

function CategoryBars({ title, data, countLabel, t }) {
  if (!data || data.length === 0) {
    return (
      <article className="panel-card">
        <h2>{title}</h2>
        <p className="panel-card__text">{t('dashboard.no_data')}</p>
      </article>
    )
  }

  return (
    <article className="panel-card">
      <h2>{title}</h2>
      <ResponsiveContainer width="100%" height={Math.max(220, data.length * 42)}>
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="category" width={112} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="count" name={countLabel} radius={[0, 6, 6, 0]}>
            {data.map((item, i) => (
              <Cell key={item.category} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {data.map((item) => (
          <div
            key={item.category}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: '1rem',
              fontSize: '0.8rem',
              textTransform: 'uppercase',
            }}
          >
            <span style={{ color: 'var(--muted)' }}>{item.category}</span>
            <span style={{ fontWeight: 700 }}>{item.count}</span>
          </div>
        ))}
      </div>
    </article>
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
  const [globalStats, setGlobalStats] = useState(null)
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
        const [alerts, news, notifications, nStats, wcloud, gStats] = await Promise.all([
          getAlerts(),
          getNews({ limit: 5 }),
          getNotifications(),
          getMyNewsStats(),
          getMyNewsWordcloud(),
          getGlobalStats(),
        ])
        if (!ignore) {
          setActiveAlertsCount(alerts.filter((a) => a.is_active).length)
          setLatestNews(news.items ? news.items.slice(0, 5) : news.slice(0, 5))
          setUnreadCount(notifications.filter((n) => !n.is_read).length)
          setNewsStats(nStats)
          setWordcloudData(wcloud)
          setGlobalStats(gStats)
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
  const globalNewsByCategory = globalStats?.news_by_category || []
  const globalAlertsByCategory = globalStats?.alerts_by_category || []
  const availableCategories = newsByCategory.map((c) => c.category)
  const userName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || t('dashboard.unknown_user')

  return (
    <section className="dashboard-page">
      <article className="panel-card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <div>
            <p className="eyebrow" style={{ marginBottom: '0.35rem' }}>{t('dashboard.global_eyebrow')}</p>
            <h2 style={{ margin: 0 }}>{t('dashboard.global_title')}</h2>
            <p className="panel-card__text" style={{ marginTop: '0.35rem', maxWidth: '56rem' }}>
              {t('dashboard.global_subtitle')}
            </p>
          </div>
          <div style={{ minWidth: '12rem', textAlign: 'right' }}>
            <p className="panel-card__text" style={{ marginBottom: '0.2rem' }}>{t('dashboard.media_outlets')}</p>
            <strong>{formatNumber(globalStats?.total_media_outlets)}</strong>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem' }}>
          <StatCard eyebrow={t('dashboard.global_sources')} value={globalStats?.total_sources} label={t('dashboard.global_sources_label')} accent="#17324d" />
          <StatCard eyebrow={t('dashboard.global_news')} value={globalStats?.total_news} label={t('dashboard.total_news_label')} accent="#bb4d00" />
          <StatCard eyebrow={t('dashboard.global_news_categories')} value={globalNewsByCategory.length} label={t('dashboard.global_news_categories_label')} accent="#2a5478" />
          <StatCard eyebrow={t('dashboard.global_alerts')} value={globalStats?.total_alerts} label={t('dashboard.global_alerts_label')} accent="#d4742e" />
          <StatCard eyebrow={t('dashboard.global_alert_categories')} value={globalAlertsByCategory.length} label={t('dashboard.global_alert_categories_label')} accent="#3d6f9e" />
        </div>
      </article>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
        <CategoryBars title={t('dashboard.global_news_by_category')} data={globalNewsByCategory} countLabel={t('dashboard.news_count')} t={t} />
        <CategoryBars title={t('dashboard.global_alerts_by_category')} data={globalAlertsByCategory} countLabel={t('dashboard.alerts_count')} t={t} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <StatCard eyebrow={t('dashboard.personal_news')} value={newsStats?.total_news} label={t('dashboard.personal_news_label')} accent="#586579" />
        <StatCard eyebrow={t('dashboard.active_alerts')} value={activeAlertsCount} label={t('dashboard.alerts_active')} accent="#8c5a2a" />
        <StatCard eyebrow={t('dashboard.unread_notifications')} value={unreadCount} label={t('dashboard.notifications_pending')} accent="#4a8ac2" />
        <article className="panel-card" style={{ textAlign: 'center', minHeight: '132px' }}>
          <p className="eyebrow" style={{ marginBottom: '0.8rem' }}>{t('dashboard.backend_status')}</p>
          {health.status === 'loading' ? <p>...</p> : null}
          {health.status === 'success' ? (
            <span className="status-pill status-pill--ok" style={{ margin: '0 auto' }}>{t('dashboard.backend_reachable')}</span>
          ) : null}
          {health.status === 'error' ? (
            <span className="status-pill status-pill--error" style={{ margin: '0 auto' }}>{t('dashboard.connection_issue')}</span>
          ) : null}
        </article>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
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
