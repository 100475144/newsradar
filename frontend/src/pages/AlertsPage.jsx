import React, { useCallback, useEffect, useReducer, useState } from 'react'
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
  return raw
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean)
}

function AlertForm({ initial, onSave, onCancel, isSubmitting, error, categories, sources }) {
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
      setSuggestionsError('Enter a keyword first to generate related terms.')
      return
    }

    setIsSuggesting(true)
    setSuggestionsError('')

    try {
      const response = await getAlertSuggestions(keyword)
      setSuggestions(response.suggestions || [])
    } catch (requestError) {
      setSuggestions([])
      setSuggestionsError(
        requestError.message || 'Unable to load keyword suggestions right now.',
      )
    } finally {
      setIsSuggesting(false)
    }
  }

  const handleSuggestionToggle = (term) => {
    setFormData((current) => {
      const currentTerms = parseExpandedKeywords(current.expanded_keywords)
      const exists = currentTerms.some(
        (item) => item.toLowerCase() === term.toLowerCase(),
      )
      const nextTerms = exists
        ? currentTerms.filter((item) => item.toLowerCase() !== term.toLowerCase())
        : [...currentTerms, term].slice(0, 10)

      return {
        ...current,
        expanded_keywords: nextTerms.join(', '),
      }
    })
  }

  const handleApplyAllSuggestions = () => {
    setFormData((current) => ({
      ...current,
      expanded_keywords: suggestions.join(', '),
    }))
  }

  const selectedSuggestions = parseExpandedKeywords(formData.expanded_keywords)

  return (
    <form className="source-form" onSubmit={handleSubmit}>
      <div className="field-grid">
        <label className="field">
          <span>Alert name</span>
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
          <span>Keyword</span>
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
          <span>IPTC Category</span>
          <select
            name="category"
            value={formData.category}
            onChange={handleChange}
            required
          >
            <option value="" disabled>Select a category...</option>
            {categories.map((cat) => (
              <option key={cat.code} value={cat.code}>
                {cat.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Related keywords (comma-separated, 3-10 if provided)</span>
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
            {isSuggesting ? 'Generating suggestions...' : 'Recommend related terms'}
          </button>

          {suggestions.length > 0 ? (
            <button
              type="button"
              className="secondary-button"
              onClick={handleApplyAllSuggestions}
              disabled={isSubmitting}
            >
              Use all suggestions
            </button>
          ) : null}
        </div>

        <p className="panel-card__text">
          Generate between 3 and 10 related terms for the current keyword, then
          click individual suggestions to add or remove them from the alert.
        </p>

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
            Monitor specific sources (leave empty for all):
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
            {sources.map((src) => (
              <label
                key={src.id}
                className="field field--inline"
                style={{ background: formData.source_ids.includes(src.id) ? 'var(--ok-soft)' : 'transparent', padding: '0.35rem 0.6rem', borderRadius: '10px', cursor: 'pointer' }}
              >
                <input
                  type="checkbox"
                  checked={formData.source_ids.includes(src.id)}
                  onChange={() => handleSourceToggle(src.id)}
                />
                <span style={{ fontSize: '0.85rem' }}>{src.name}</span>
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
          <span>In-app notifications</span>
        </label>
        <label className="field field--inline">
          <input
            type="checkbox"
            name="notify_email"
            checked={formData.notify_email}
            onChange={handleChange}
          />
          <span>Email notifications</span>
        </label>
      </div>

      {error ? <p className="form-message form-message--error">{error}</p> : null}

      <div className="source-form__actions">
        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : initial ? 'Save changes' : 'Add alert'}
        </button>
        <button type="button" className="secondary-button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}

function AlertRow({ alert, onEdit, onDelete, onToggle, busy }) {
  return (
    <div className="source-row">
      <div className="source-row__info">
        <strong className="source-row__name">{alert.name}</strong>
        <span className="source-row__url">
          Keyword: <em>{alert.keyword}</em> &mdash; Category: <em>{alert.category}</em>
        </span>
        {alert.expanded_keywords && alert.expanded_keywords.length > 0 ? (
          <span className="source-row__url">
            Related: {alert.expanded_keywords.join(', ')}
          </span>
        ) : null}
        {alert.source_ids && alert.source_ids.length > 0 ? (
          <span className="source-row__url">
            Sources: {alert.source_ids.length} selected
          </span>
        ) : (
          <span className="source-row__url">Sources: all</span>
        )}
        <span className="source-row__url">
          {alert.notify_in_app ? 'In-app' : null}
          {alert.notify_in_app && alert.notify_email ? ' · ' : null}
          {alert.notify_email ? 'Email' : null}
          {!alert.notify_in_app && !alert.notify_email ? 'No notifications' : null}
        </span>
      </div>

      <span
        className={
          alert.is_active
            ? 'source-badge source-badge--active'
            : 'source-badge source-badge--inactive'
        }
      >
        {alert.is_active ? 'Active' : 'Inactive'}
      </span>

      <div className="source-row__actions">
        <button
          type="button"
          className="secondary-button"
          onClick={() => onToggle(alert)}
          disabled={busy}
        >
          {alert.is_active ? 'Deactivate' : 'Activate'}
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={() => onEdit(alert)}
          disabled={busy}
        >
          Edit
        </button>
        <button
          type="button"
          className="danger-button"
          onClick={() => onDelete(alert.id)}
          disabled={busy}
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default function AlertsPage() {
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

  useEffect(() => {
    load()
  }, [load])

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
    if (!window.confirm('Delete this alert? This cannot be undone.')) return
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

  const openAdd = () => {
    setEditing(null)
    setFormError('')
    setShowForm(true)
  }

  const openEdit = (alert) => {
    setEditing(alert)
    setFormError('')
    setShowForm(false)
  }

  const cancelForm = () => {
    setShowForm(false)
    setEditing(null)
    setFormError('')
  }

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">Alerts</p>
        <h1>Your alerts</h1>
        <p>
          Define keywords and IPTC categories to watch. NewsRadar will match incoming
          articles against your active alerts and notify you accordingly.
        </p>
      </div>

      <div className="sources-toolbar">
        {!showForm && !editing ? (
          <button type="button" className="primary-button" onClick={openAdd}>
            + Add alert
          </button>
        ) : null}
      </div>

      {showForm ? (
        <div className="panel-card">
          <h2>New alert</h2>
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
        <p className="sources-feedback">Loading alerts...</p>
      ) : null}

      {state.status === 'error' ? (
        <p className="form-message form-message--error">{state.error}</p>
      ) : null}

      {state.status === 'success' && state.items.length === 0 ? (
        <div className="panel-card sources-empty">
          <p>No alerts yet. Create your first alert above.</p>
        </div>
      ) : null}

      {state.status === 'success' && state.items.length > 0 ? (
        <div className="sources-list">
          {state.items.map((alert) =>
            editing?.id === alert.id ? (
              <div key={alert.id} className="panel-card">
                <h2>Edit alert</h2>
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
              />
            ),
          )}
        </div>
      ) : null}
    </section>
  )
}
