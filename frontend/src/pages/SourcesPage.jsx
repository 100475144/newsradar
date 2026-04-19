import React, { useCallback, useEffect, useReducer, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  createSource,
  deleteSource,
  getSources,
  getSourcesCatalogSummary,
  updateSource,
} from '../api/sourcesApi'
import { request } from '../api/client'
import { useAuth } from '../context/AuthContext'

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
  const { t } = useTranslation()
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
          <span>{t('sources.medium')}</span>
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
          <span>{t('sources.channel')}</span>
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
          <span>{t('sources.rss_url')}</span>
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
          <span>{t('sources.iptc_category')}</span>
          <select name="category" value={formData.category} onChange={handleChange} required>
            <option value="" disabled>{t('sources.select_category')}</option>
            {categories.map((category) => (
              <option key={category.code} value={category.code}>{category.label}</option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="form-message form-message--error">{error}</p> : null}

      <div className="source-form__actions">
        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? t('sources.saving') : initial ? t('sources.save_changes') : t('sources.add')}
        </button>
        <button type="button" className="secondary-button" onClick={onCancel}>
          {t('sources.cancel')}
        </button>
      </div>
    </form>
  )
}

function SourceRow({ source, onEdit, onDelete, onToggle, busy, categories, canEdit }) {
  const { t } = useTranslation()

  return (
    <div className="source-row">
      <div className="source-row__info">
        <strong className="source-row__name">
          {source.medium_name} - {source.name}
        </strong>
        <span className="source-row__url">{t('sources.medium_col')}: {source.medium_name}</span>
        <span className="source-row__url">{t('sources.channel_col')}: {source.name}</span>
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
            {t('sources.category_col')}: {formatCategoryLabel(source.category, categories)}
          </span>
        ) : null}
      </div>

      <span className={source.is_active ? 'source-badge source-badge--active' : 'source-badge source-badge--inactive'}>
        {source.is_active ? t('sources.active') : t('sources.inactive')}
      </span>

      {canEdit ? (
        <div className="source-row__actions">
          <button type="button" className="secondary-button" onClick={() => onToggle(source)} disabled={busy}>
            {source.is_active ? t('sources.deactivate') : t('sources.activate')}
          </button>
          <button type="button" className="secondary-button" onClick={() => onEdit(source)} disabled={busy}>
            {t('sources.edit')}
          </button>
          <button type="button" className="danger-button" onClick={() => onDelete(source.id)} disabled={busy}>
            {t('sources.delete')}
          </button>
        </div>
      ) : null}
    </div>
  )
}

export default function SourcesPage() {
  const { user } = useAuth()
  const { t } = useTranslation()
  const canEdit = user?.role !== 'lector'
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

  useEffect(() => { load() }, [load])

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
      const updated = await updateSource(editing.id, { ...formData, is_active: editing.is_active })
      dispatch({ type: 'UPDATE', item: updated })
      setEditing(null)
    } catch (error) {
      setFormError(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('sources.delete_confirm'))) return
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

  const openAdd = () => { setEditing(null); setFormError(''); setShowForm(true) }
  const openEdit = (source) => { setEditing(source); setFormError(''); setShowForm(false) }
  const cancelForm = () => { setShowForm(false); setEditing(null); setFormError('') }

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">{t('sources.eyebrow')}</p>
        <h1>{t('sources.title')}</h1>
        <p>{t('sources.subtitle')}</p>
      </div>

      {catalogSummary ? (
        <div className="panel-card">
          <h2>{t('sources.default_catalog')}</h2>
          <dl className="detail-list">
            <div>
              <dt>{t('sources.initial_channels')}</dt>
              <dd>{catalogSummary.total_channels}</dd>
            </div>
            <div>
              <dt>{t('sources.media_outlets')}</dt>
              <dd>{catalogSummary.total_media_outlets}</dd>
            </div>
            <div>
              <dt>{t('sources.iptc_coverage')}</dt>
              <dd>{catalogSummary.iptc_categories_covered} / {catalogSummary.iptc_categories_total}</dd>
            </div>
            <div>
              <dt>{t('sources.status')}</dt>
              <dd>
                {catalogSummary.covers_all_iptc_categories
                  ? t('sources.all_covered')
                  : t('sources.coverage_incomplete')}
              </dd>
            </div>
          </dl>
        </div>
      ) : null}

      <div className="sources-toolbar">
        {canEdit && !showForm && !editing ? (
          <button type="button" className="primary-button" onClick={openAdd}>
            {t('sources.add_source')}
          </button>
        ) : null}
      </div>

      {showForm ? (
        <div className="panel-card">
          <h2>{t('sources.new_source')}</h2>
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
        <p className="sources-feedback">{t('sources.loading')}</p>
      ) : null}

      {state.status === 'error' ? (
        <p className="form-message form-message--error">{state.error}</p>
      ) : null}

      {state.status === 'success' && state.items.length === 0 ? (
        <div className="panel-card sources-empty">
          <p>{t('sources.empty')}</p>
        </div>
      ) : null}

      {state.status === 'success' && state.items.length > 0 ? (
        <div className="sources-list">
          {state.items.map((source) =>
            editing?.id === source.id ? (
              <div key={source.id} className="panel-card">
                <h2>{t('sources.edit_source')}</h2>
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
                canEdit={canEdit}
              />
            ),
          )}
        </div>
      ) : null}
    </section>
  )
}
