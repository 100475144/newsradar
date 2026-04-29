import React, { useCallback, useEffect, useReducer, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  activateAlert,
  createAlert,
  deactivateAlert,
  deleteAlert,
  getAlerts,
  getAlertSuggestions,
  updateAlert,
} from '../api/alertsApi'
import { getSources } from '../api/sourcesApi'
import { request } from '../api/client'

const INITIAL_FORM = {
  name: '',
  keyword: '',
  category: '',
  expanded_keywords: '',
  source_ids: [],
  notify_in_app: true,
  notify_email: false,
}

function alertsReducer(state, action) {
  switch (action.type) {
    case 'LOADING':
      return { ...state, status: 'loading', error: '' }
    case 'LOADED':
      return { status: 'success', items: action.items, error: '' }
    case 'ERROR':
      return { ...state, status: 'error', error: action.error }
    case 'ADD':
      return { ...state, items: [...state.items, action.item] }
    case 'UPDATE':
      return {
        ...state,
        items: state.items.map((a) => (a.id === action.item.id ? action.item : a)),
      }
    case 'REMOVE':
      return { ...state, items: state.items.filter((a) => a.id !== action.id) }
    default:
      return state
  }
}

function parseExpandedKeywords(raw) {
  if (!raw || !raw.trim()) return []
  return raw.split(',').map((k) => k.trim()).filter(Boolean)
}

function formatSourceLabel(source) {
  if (!source.medium_name) return source.name
  return `${source.medium_name} - ${source.name}`
}

function AlertForm({ initial, onSave, onCancel, isSubmitting, error, categories, sources }) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState(
    initial
      ? {
          ...initial,
          expanded_keywords: (initial.expanded_keywords || []).join(', '),
          source_ids: initial.source_ids || [],
        }
      : INITIAL_FORM,
  )
  const [suggestions, setSuggestions] = useState([])
  const [suggestionsError, setSuggestionsError] = useState('')
  const [isSuggesting, setIsSuggesting] = useState(false)

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    if (name === 'keyword') {
      setSuggestions([])
      setSuggestionsError('')
    }
    setFormData((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSourceToggle = (sourceId) => {
    setFormData((current) => {
      const ids = current.source_ids.includes(sourceId)
        ? current.source_ids.filter((id) => id !== sourceId)
        : [...current.source_ids, sourceId]
      return { ...current, source_ids: ids }
    })
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const payload = {
      ...formData,
      expanded_keywords: parseExpandedKeywords(formData.expanded_keywords),
    }
    onSave(payload)
  }

  const handleSuggest = async () => {
    const keyword = formData.keyword.trim()
    if (!keyword) {
      setSuggestions([])
      setSuggestionsError(t('alerts.enter_keyword_first'))
      return
    }
    setIsSuggesting(true)
    setSuggestionsError('')
    try {
      const response = await getAlertSuggestions(keyword)
      setSuggestions(response.suggestions || [])
    } catch (requestError) {
      setSuggestions([])
      setSuggestionsError(requestError.message || 'Unable to load keyword suggestions right now.')
    } finally {
      setIsSuggesting(false)
    }
  }

  const handleSuggestionToggle = (term) => {
    setFormData((current) => {
      const currentTerms = parseExpandedKeywords(current.expanded_keywords)
      const exists = currentTerms.some((item) => item.toLowerCase() === term.toLowerCase())
      const nextTerms = exists
        ? currentTerms.filter((item) => item.toLowerCase() !== term.toLowerCase())
        : [...currentTerms, term].slice(0, 10)
      return { ...current, expanded_keywords: nextTerms.join(', ') }
    })
  }

  const handleApplyAllSuggestions = () => {
    setFormData((current) => ({ ...current, expanded_keywords: suggestions.join(', ') }))
  }

  const selectedSuggestions = parseExpandedKeywords(formData.expanded_keywords)

  return (
    <form className="source-form" onSubmit={handleSubmit}>
      <div className="field-grid">
        <label className="field">
          <span>{t('alerts.alert_name')}</span>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Tech news alert"
            required
          />
        </label>
        <label className="field">
          <span>{t('alerts.keyword')}</span>
          <input
            type="text"
            name="keyword"
            value={formData.keyword}
            onChange={handleChange}
            placeholder="artificial intelligence"
            required
          />
        </label>
        <label className="field">
          <span>{t('alerts.iptc_category')}</span>
          <select name="category" value={formData.category} onChange={handleChange} required>
            <option value="" disabled>{t('alerts.select_category')}</option>
            {categories.map((cat) => (
              <option key={cat.code} value={cat.code}>{cat.label}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>{t('alerts.related_keywords')}</span>
          <input
            type="text"
            name="expanded_keywords"
            value={formData.expanded_keywords}
            onChange={handleChange}
            placeholder="machine learning, neural networks, deep learning"
          />
        </label>
      </div>

      <div className="alert-suggestions">
        <div className="alert-suggestions__toolbar">
          <button
            type="button"
            className="secondary-button"
            onClick={handleSuggest}
            disabled={isSubmitting || isSuggesting}
          >
            {isSuggesting ? t('alerts.generating') : t('alerts.recommend')}
          </button>
          {suggestions.length > 0 ? (
            <button
              type="button"
              className="secondary-button"
              onClick={handleApplyAllSuggestions}
              disabled={isSubmitting}
            >
              {t('alerts.use_all')}
            </button>
          ) : null}
        </div>

        <p className="panel-card__text">{t('alerts.suggestions_info')}</p>

        {suggestionsError ? (
          <p className="form-message form-message--error">{suggestionsError}</p>
        ) : null}

        {suggestions.length > 0 ? (
          <div className="alert-suggestions__list">
            {suggestions.map((term) => {
              const isSelected = selectedSuggestions.some(
                (item) => item.toLowerCase() === term.toLowerCase(),
              )
              return (
                <button
                  key={term}
                  type="button"
                  className={
                    isSelected
                      ? 'alert-suggestion-chip alert-suggestion-chip--active'
                      : 'alert-suggestion-chip'
                  }
                  onClick={() => handleSuggestionToggle(term)}
                >
                  {term}
                </button>
              )
            })}
          </div>
        ) : null}
      </div>

      {sources.length > 0 ? (
        <div style={{ marginTop: '0.5rem' }}>
          <span style={{ fontWeight: 700, fontSize: '0.92rem' }}>
            {t('alerts.monitor_sources')}
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
            {sources.map((src) => (
              <label
                key={src.id}
                className="field field--inline"
                style={{
                  background: formData.source_ids.includes(src.id) ? 'var(--ok-soft)' : 'transparent',
                  padding: '0.35rem 0.6rem',
                  borderRadius: '10px',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={formData.source_ids.includes(src.id)}
                  onChange={() => handleSourceToggle(src.id)}
                />
                <span style={{ fontSize: '0.85rem' }}>{formatSourceLabel(src)}</span>
              </label>
            ))}
          </div>
        </div>
      ) : null}

      <div className="source-form__actions" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
        <label className="field field--inline">
          <input
            type="checkbox"
            name="notify_in_app"
            checked={formData.notify_in_app}
            onChange={handleChange}
          />
          <span>{t('alerts.in_app')}</span>
        </label>
        <label className="field field--inline">
          <input
            type="checkbox"
            name="notify_email"
            checked={formData.notify_email}
            onChange={handleChange}
          />
          <span>{t('alerts.email_notif')}</span>
        </label>
      </div>

      {error ? <p className="form-message form-message--error">{error}</p> : null}

      <div className="source-form__actions">
        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? t('alerts.saving') : initial ? t('alerts.save_changes') : t('alerts.add')}
        </button>
        <button type="button" className="secondary-button" onClick={onCancel}>
          {t('alerts.cancel')}
        </button>
      </div>
    </form>
  )
}

function AlertRow({ alert, onEdit, onDelete, onToggle, busy, canEdit }) {
  const { t } = useTranslation()

  return (
    <div className="source-row">
      <div className="source-row__info">
        <strong className="source-row__name">{alert.name}</strong>
        <span className="source-row__url">
          {t('alerts.keyword')}: <em>{alert.keyword}</em> &mdash; {t('alerts.iptc_category')}: <em>{alert.category}</em>
        </span>
        {alert.expanded_keywords && alert.expanded_keywords.length > 0 ? (
          <span className="source-row__url">
            Related: {alert.expanded_keywords.join(', ')}
          </span>
        ) : null}
        {alert.source_ids && alert.source_ids.length > 0 ? (
          <span className="source-row__url">
            {t('alerts.sources_selected', { count: alert.source_ids.length })}
          </span>
        ) : (
          <span className="source-row__url">{t('alerts.sources_all')}</span>
        )}
        <span className="source-row__url">
          {alert.notify_in_app ? t('alerts.in_app') : null}
          {alert.notify_in_app && alert.notify_email ? ' · ' : null}
          {alert.notify_email ? t('alerts.email_notif') : null}
          {!alert.notify_in_app && !alert.notify_email ? t('alerts.no_notifications_config') : null}
        </span>
      </div>

      <span className={alert.is_active ? 'source-badge source-badge--active' : 'source-badge source-badge--inactive'}>
        {alert.is_active ? t('alerts.active') : t('alerts.inactive')}
      </span>

      {canEdit ? (
        <div className="source-row__actions">
          <button type="button" className="secondary-button" onClick={() => onToggle(alert)} disabled={busy}>
            {alert.is_active ? t('alerts.deactivate') : t('alerts.activate')}
          </button>
          <button type="button" className="secondary-button" onClick={() => onEdit(alert)} disabled={busy}>
            {t('alerts.edit')}
          </button>
          <button type="button" className="danger-button" onClick={() => onDelete(alert.id)} disabled={busy}>
            {t('alerts.delete')}
          </button>
        </div>
      ) : null}
    </div>
  )
}

export default function AlertsPage() {
  const { t } = useTranslation()
  // El rol "lector" se eliminó por adenda oficial: todos los autenticados son gestores.
  const canEdit = true
  const [state, dispatch] = useReducer(alertsReducer, {
    status: 'loading',
    items: [],
    error: '',
  })
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [formError, setFormError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [busyId, setBusyId] = useState(null)
  const [categories, setCategories] = useState([])
  const [sources, setSources] = useState([])

  const load = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const [items, cats, srcs] = await Promise.all([
        getAlerts(),
        request('/alerts/categories'),
        getSources(),
      ])
      dispatch({ type: 'LOADED', items })
      setCategories(cats)
      setSources(srcs)
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleAdd = async (formData) => {
    setFormError('')
    setIsSubmitting(true)
    try {
      const created = await createAlert(formData)
      dispatch({ type: 'ADD', item: created })
      setShowForm(false)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdate = async (formData) => {
    setFormError('')
    setIsSubmitting(true)
    try {
      const updated = await updateAlert(editing.id, formData)
      dispatch({ type: 'UPDATE', item: updated })
      setEditing(null)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('alerts.delete_confirm'))) return
    setBusyId(id)
    try {
      await deleteAlert(id)
      dispatch({ type: 'REMOVE', id })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    } finally {
      setBusyId(null)
    }
  }

  const handleToggle = async (alert) => {
    setBusyId(alert.id)
    try {
      const updated = alert.is_active
        ? await deactivateAlert(alert.id)
        : await activateAlert(alert.id)
      dispatch({ type: 'UPDATE', item: updated })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    } finally {
      setBusyId(null)
    }
  }

  const openAdd = () => { setEditing(null); setFormError(''); setShowForm(true) }
  const openEdit = (alert) => { setEditing(alert); setFormError(''); setShowForm(false) }
  const cancelForm = () => { setShowForm(false); setEditing(null); setFormError('') }

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">{t('alerts.eyebrow')}</p>
        <h1>{t('alerts.title')}</h1>
        <p>{t('alerts.subtitle')}</p>
      </div>

      <div className="sources-toolbar">
        {canEdit && !showForm && !editing ? (
          <button type="button" className="primary-button" onClick={openAdd}>
            {t('alerts.add_alert')}
          </button>
        ) : null}
      </div>

      {showForm ? (
        <div className="panel-card">
          <h2>{t('alerts.new_alert')}</h2>
          <AlertForm
            onSave={handleAdd}
            onCancel={cancelForm}
            isSubmitting={isSubmitting}
            error={formError}
            categories={categories}
            sources={sources}
          />
        </div>
      ) : null}

      {state.status === 'loading' ? (
        <p className="sources-feedback">{t('alerts.loading')}</p>
      ) : null}

      {state.status === 'error' ? (
        <p className="form-message form-message--error">{state.error}</p>
      ) : null}

      {state.status === 'success' && state.items.length === 0 ? (
        <div className="panel-card sources-empty">
          <p>{t('alerts.empty')}</p>
        </div>
      ) : null}

      {state.status === 'success' && state.items.length > 0 ? (
        <div className="sources-list">
          {state.items.map((alert) =>
            editing?.id === alert.id ? (
              <div key={alert.id} className="panel-card">
                <h2>{t('alerts.edit_alert')}</h2>
                <AlertForm
                  initial={alert}
                  onSave={handleUpdate}
                  onCancel={cancelForm}
                  isSubmitting={isSubmitting}
                  error={formError}
                  categories={categories}
                  sources={sources}
                />
              </div>
            ) : (
              <AlertRow
                key={alert.id}
                alert={alert}
                onEdit={openEdit}
                onDelete={handleDelete}
                onToggle={handleToggle}
                busy={busyId === alert.id}
                canEdit={canEdit}
              />
            ),
          )}
        </div>
      ) : null}
    </section>
  )
}
