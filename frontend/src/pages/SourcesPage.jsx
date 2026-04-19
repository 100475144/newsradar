import React, { useCallback, useEffect, useReducer, useState } from 'react'
import {
  createSource,
  deleteSource,
  getSources,
  getSourcesCatalogSummary,
  updateSource,
} from '../api/sourcesApi'
import { request } from '../api/client'

const INITIAL_FORM = {
  medium_name: '',
  name: '',
  url: '',
  category: '',
}

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
        items: state.items.map((source) => (source.id === action.item.id ? action.item : source)),
      }
    case 'REMOVE':
      return { ...state, items: state.items.filter((source) => source.id !== action.id) }
    default:
      return state
  }
}

function formatCategoryLabel(category, categories) {
  const match = categories.find((item) => item.code === category)
  return match ? match.label : category
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
          <span>Medium / Outlet</span>
          <input
            type="text"
            name="medium_name"
            value={formData.medium_name}
            onChange={handleChange}
            placeholder="BBC"
            required
          />
        </label>
        <label className="field">
          <span>Channel name</span>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Technology"
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
            placeholder="https://feeds.bbci.co.uk/news/technology/rss.xml"
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
            {categories.map((category) => (
              <option key={category.code} value={category.code}>
                {category.label}
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

function SourceRow({ source, onEdit, onDelete, onToggle, busy, categories }) {
  return (
    <div className="source-row">
      <div className="source-row__info">
        <strong className="source-row__name">
          {source.medium_name} - {source.name}
        </strong>
        <span className="source-row__url">Medium: {source.medium_name}</span>
        <span className="source-row__url">Channel: {source.name}</span>
        <a
          className="source-row__url"
          href={source.url}
          target="_blank"
          rel="noreferrer noopener"
        >
          {source.url}
        </a>
        {source.category ? (
          <span className="source-row__url">
            Category: {formatCategoryLabel(source.category, categories)}
          </span>
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
  const [catalogSummary, setCatalogSummary] = useState(null)

  const load = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const [items, catalog, cats] = await Promise.all([
        getSources(),
        getSourcesCatalogSummary(),
        request('/alerts/categories'),
      ])
      dispatch({ type: 'LOADED', items })
      setCatalogSummary(catalog)
      setCategories(cats)
    } catch (error) {
      dispatch({ type: 'ERROR', error: error.message })
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
    } catch (error) {
      setFormError(error.message)
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
    } catch (error) {
      setFormError(error.message)
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
    } catch (error) {
      dispatch({ type: 'ERROR', error: error.message })
    } finally {
      setBusyId(null)
    }
  }

  const handleToggle = async (source) => {
    setBusyId(source.id)
    try {
      const updated = await updateSource(source.id, {
        medium_name: source.medium_name,
        name: source.name,
        url: source.url,
        category: source.category,
        is_active: !source.is_active,
      })
      dispatch({ type: 'UPDATE', item: updated })
    } catch (error) {
      dispatch({ type: 'ERROR', error: error.message })
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
          Every user receives the default NewsRadar catalog on first access, and you
          can also create extra RSS channels explicitly linked to a media outlet and
          an IPTC category.
        </p>
      </div>

      {catalogSummary ? (
        <div className="panel-card">
          <h2>Default catalog</h2>
          <dl className="detail-list">
            <div>
              <dt>Initial channels</dt>
              <dd>{catalogSummary.total_channels}</dd>
            </div>
            <div>
              <dt>Media outlets</dt>
              <dd>{catalogSummary.total_media_outlets}</dd>
            </div>
            <div>
              <dt>IPTC coverage</dt>
              <dd>
                {catalogSummary.iptc_categories_covered} / {catalogSummary.iptc_categories_total}
              </dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                {catalogSummary.covers_all_iptc_categories
                  ? 'All first-level IPTC categories covered'
                  : 'Coverage incomplete'}
              </dd>
            </div>
          </dl>
        </div>
      ) : null}

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
                  initial={{
                    medium_name: source.medium_name,
                    name: source.name,
                    url: source.url,
                    category: source.category || '',
                  }}
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
                categories={categories}
              />
            ),
          )}
        </div>
      ) : null}
    </section>
  )
}
