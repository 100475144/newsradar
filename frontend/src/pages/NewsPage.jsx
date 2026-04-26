import React, { useCallback, useEffect, useReducer, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getNews } from '../api/newsApi'

const PAGE_SIZE = 20

function newsReducer(state, action) {
  switch (action.type) {
    case 'LOADING':
      return { ...state, status: 'loading', error: '' }
    case 'LOADED':
      return { status: 'success', items: action.items, total: action.total, error: '' }
    case 'ERROR':
      return { ...state, status: 'error', error: action.error }
    default:
      return state
  }
}

function NewsRow({ news }) {
  const { t } = useTranslation()

  function formatClassificationOrigin(origin) {
    switch ((origin || '').toLowerCase()) {
      case 'alert': return t('news.classified_alert')
      case 'source': return t('news.classified_source')
      case 'rss': return t('news.classified_rss')
      default: return t('news.classified_pending')
    }
  }

  const date = news.published_at
    ? new Date(news.published_at).toLocaleString()
    : t('news.unknown_date')

  return (
    <div className="source-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%' }}>
        <strong className="source-row__name" style={{ flex: 1 }}>{news.title}</strong>
        {news.category ? (
          <span className="source-badge source-badge--active">{news.category}</span>
        ) : null}
      </div>
      <span className="source-row__url">
        {formatClassificationOrigin(news.classification_origin)}
      </span>
      {news.summary ? (
        <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: 0, lineHeight: 1.5 }}>
          {news.summary.length > 250 ? news.summary.slice(0, 250) + '...' : news.summary}
        </p>
      ) : null}
      <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: 'var(--muted)' }}>
        <span>{date}</span>
        {news.author ? <span>{t('news.by_author', { author: news.author })}</span> : null}
        <a href={news.link} target="_blank" rel="noreferrer noopener" style={{ color: 'var(--accent)' }}>
          {t('news.read_original')}
        </a>
      </div>
    </div>
  )
}

export default function NewsPage() {
  const { t } = useTranslation()
  const [state, dispatch] = useReducer(newsReducer, {
    status: 'loading',
    items: [],
    total: 0,
    error: '',
  })
  const [page, setPage] = useState(0)
  const [filterCategory, setFilterCategory] = useState('')

  const load = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const result = await getNews({
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
        category: filterCategory || undefined,
      })
      dispatch({ type: 'LOADED', items: result.items, total: result.total })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    }
  }, [page, filterCategory])

  useEffect(() => {
    load()
  }, [load])

  const totalPages = Math.ceil(state.total / PAGE_SIZE)

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">{t('news.eyebrow')}</p>
        <h1>{t('news.title')}</h1>
        <p>{t('news.subtitle')}</p>
      </div>

      <div className="sources-toolbar" style={{ gap: '0.75rem', flexWrap: 'wrap' }}>
        <label className="field" style={{ minWidth: '14rem' }}>
          <span>{t('news.filter_category')}</span>
          <input
            type="text"
            value={filterCategory}
            onChange={(e) => { setFilterCategory(e.target.value); setPage(0) }}
            placeholder={t('news.filter_placeholder')}
          />
        </label>
        <span style={{ alignSelf: 'flex-end', padding: '0.95rem 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
          {t('news.articles_found', { count: state.total })}
        </span>
      </div>

      {state.status === 'loading' ? (
        <p className="sources-feedback">{t('news.loading')}</p>
      ) : null}

      {state.status === 'error' ? (
        <p className="form-message form-message--error">{state.error}</p>
      ) : null}

      {state.status === 'success' && state.items.length === 0 ? (
        <div className="panel-card sources-empty">
          <p>{t('news.empty')}</p>
        </div>
      ) : null}

      {state.status === 'success' && state.items.length > 0 ? (
        <>
          <div className="sources-list">
            {state.items.map((news) => (
              <NewsRow key={news.id} news={news} />
            ))}
          </div>

          {totalPages > 1 ? (
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1rem' }}>
              <button
                className="secondary-button"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                {t('news.previous')}
              </button>
              <span style={{ padding: '0.95rem 0.5rem', color: 'var(--muted)' }}>
                {t('news.page_of', { current: page + 1, total: totalPages })}
              </span>
              <button
                className="secondary-button"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                {t('news.next')}
              </button>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  )
}
