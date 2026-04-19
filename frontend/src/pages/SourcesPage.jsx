import React, { useCallback, useEffect, useReducer, useState } from 'react'
import { createSource, deleteSource, getSources, updateSource } from '../api/sourcesApi'
import { request } from '../api/client'

const INITIAL_FORM = { name: '', url: '', category: '' }

function sourcesReducer(state, action) {
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
        items: state.items.map((s) => (s.id === action.item.id ? action.item : s)),
      }
    case 'REMOVE':
      return { ...state, items: state.items.filter((s) => s.id !== action.id) }
    default:
      return state
  }
}

function SourceForm({ initial, onSave, onCancel, isSubmitting, error, categories }) {
  const [formData, setFormData] = useState(initial || INITIAL_FORM)

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    onSave(formData)
  }

  return (
    <form className="source-form" onSubmit={handleSubmit}>
      <div className="field-grid">
        <label className="field">
          <span>Name</span>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="BBC News"
            required
          />
        </label>
        <label className="field">
          <span>RSS URL</span>
          <input
            type="url"
            name="url"
            value={formData.url}
            onChange={handleChange}
            placeholder="https://feeds.bbci.co.uk/news/rss.xml"
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
      </div>

      {error ? <p className="form-message form-message--error">{error}</p> : null}

      <div className="source-form__actions">
        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : initial ? 'Save changes' : 'Add source'}
        </button>
        <button type="button" className="secondary-button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}

function SourceRow({ source, onEdit, onDelete, onToggle, busy }) {
  return (
    <div className="source-row">
      <div className="source-row__info">
        <strong className="source-row__name">{source.name}</strong>
        <a
          className="source-row__url"
          href={source.url}
          target="_blank"
          rel="noreferrer noopener"
        >
          {source.url}
        </a>
        {source.category ? (
          <span className="source-row__url">Category: {source.category}</span>
        ) : null}
      </div>

      <span
        className={
          source.is_active
            ? 'source-badge source-badge--active'
            : 'source-badge source-badge--inactive'
        }
      >
        {source.is_active ? 'Active' : 'Inactive'}
      </span>

      <div className="source-row__actions">
        <button
          type="button"
          className="secondary-button"
          onClick={() => onToggle(source)}
          disabled={busy}
        >
          {source.is_active ? 'Deactivate' : 'Activate'}
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={() => onEdit(source)}
          disabled={busy}
        >
          Edit
        </button>
        <button
          type="button"
          className="danger-button"
          onClick={() => onDelete(source.id)}
          disabled={busy}
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default function SourcesPage() {
  const [state, dispatch] = useReducer(sourcesReducer, {
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

  const load = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const [items, cats] = await Promise.all([
        getSources(),
        request('/alerts/categories'),
      ])
      dispatch({ type: 'LOADED', items })
      setCategories(cats)
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
      const created = await createSource(formData)
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
      const updated = await updateSource(editing.id, {
        ...formData,
        is_active: editing.is_active,
      })
      dispatch({ type: 'UPDATE', item: updated })
      setEditing(null)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this source? This cannot be undone.')) return
    setBusyId(id)
    try {
      await deleteSource(id)
      dispatch({ type: 'REMOVE', id })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message })
    } finally {
      setBusyId(null)
    }
  }

  const handleToggle = async (source) => {
    setBusyId(source.id)
    try {
      const updated = await updateSource(source.id, {
        name: source.name,
        url: source.url,
        category: source.category,
        is_active: !source.is_active,
      })
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

  const openEdit = (source) => {
    setEditing(source)
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
        <p className="eyebrow">RSS Feeds</p>
        <h1>Your sources</h1>
        <p>
          Manage the RSS feeds that NewsRadar monitors. Active sources are crawled
          automatically to bring new articles into your dashboard.
        </p>
      </div>

      <div className="sources-toolbar">
        {!showForm && !editing ? (
          <button type="button" className="primary-button" onClick={openAdd}>
            + Add source
          </button>
        ) : null}
      </div>

      {showForm ? (
        <div className="panel-card">
          <h2>New source</h2>
          <SourceForm
            onSave={handleAdd}
            onCancel={cancelForm}
            isSubmitting={isSubmitting}
            error={formError}
            categories={categories}
          />
        </div>
      ) : null}

      {state.status === 'loading' ? (
        <p className="sources-feedback">Loading sources...</p>
      ) : null}

      {state.status === 'error' ? (
        <p className="form-message form-message--error">{state.error}</p>
      ) : null}

      {state.status === 'success' && state.items.length === 0 ? (
        <div className="panel-card sources-empty">
          <p>No sources yet. Add your first RSS feed above.</p>
        </div>
      ) : null}

      {state.status === 'success' && state.items.length > 0 ? (
        <div className="sources-list">
          {state.items.map((source) =>
            editing?.id === source.id ? (
              <div key={source.id} className="panel-card">
                <h2>Edit source</h2>
                <SourceForm
                  initial={{ name: source.name, url: source.url, category: source.category || '' }}
                  onSave={handleUpdate}
                  onCancel={cancelForm}
                  isSubmitting={isSubmitting}
                  error={formError}
                  categories={categories}
                />
              </div>
            ) : (
              <SourceRow
                key={source.id}
                source={source}
                onEdit={openEdit}
                onDelete={handleDelete}
                onToggle={handleToggle}
                busy={busyId === source.id}
              />
            ),
          )}
        </div>
      ) : null}
    </section>
  )
}
