import React, { useCallback, useEffect, useReducer, useState } from 'react'
import {
  activateAlert,
  createAlert,
  deactivateAlert,
  deleteAlert,
  getAlerts,
  updateAlert,
} from '../api/alertsApi'

const CATEGORIES = [
  { value: 'technology', label: 'Technology' },
  { value: 'politics', label: 'Politics' },
  { value: 'business', label: 'Business' },
  { value: 'science', label: 'Science' },
  { value: 'health', label: 'Health' },
  { value: 'sports', label: 'Sports' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'world', label: 'World' },
  { value: 'environment', label: 'Environment' },
  { value: 'economy', label: 'Economy' },
]

const INITIAL_FORM = {
  name: '',
  keyword: '',
  category: '',
  expanded_keywords: '',
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

function AlertForm({ initial, onSave, onCancel, isSubmitting, error }) {
  const [formData, setFormData] = useState(
    initial
      ? {
          ...initial,
          expanded_keywords: (initial.expanded_keywords || []).join(', '),
        }
      : INITIAL_FORM,
  )

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setFormData((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const payload = {
      ...formData,
      expanded_keywords: parseExpandedKeywords(formData.expanded_keywords),
    }
    onSave(payload)
  }

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
          <span>Category</span>
          <select
            name="category"
            value={formData.category}
            onChange={handleChange}
            required
          >
            <option value="" disabled>Select a category…</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Related keywords (comma-separated, 3–10 if provided)</span>
          <input
            type="text"
            name="expanded_keywords"
            value={formData.expanded_keywords}
            onChange={handleChange}
            placeholder="machine learning, neural networks, deep learning"
          />
        </label>
      </div>

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

  const load = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const items = await getAlerts()
      dispatch({ type: 'LOADED', items })
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
          Define keywords and categories to watch. NewsRadar will match incoming
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
