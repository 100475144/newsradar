import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import {
  activateRssChannel,
  createInformationSource,
  createRssChannel,
  deactivateRssChannel,
  deleteInformationSource,
  deleteRssChannel,
  getCategories,
  getInformationSources,
  getRssChannelsForSource,
  getSourcesCatalogSummary,
  updateInformationSource,
  updateRssChannel,
} from '../api/sourcesApi'

const EMPTY_MEDIUM = { name: '', url: '' }
const EMPTY_CHANNEL = { url: '', category_id: '', information_source_id: '' }

function MediumForm({ initial, onSave, onCancel, isSubmitting, error }) {
  const { t } = useTranslation()
  const [data, setData] = useState(initial || EMPTY_MEDIUM)

  const change = (e) => setData({ ...data, [e.target.name]: e.target.value })
  const submit = (e) => {
    e.preventDefault()
    onSave(data)
  }

  return (
    <form className="source-form" onSubmit={submit}>
      <div className="field-grid">
        <label className="field">
          <span>{t('sources.medium')}</span>
          <input type="text" name="name" value={data.name} onChange={change} required placeholder="BBC" />
        </label>
        <label className="field">
          <span>URL</span>
          <input type="url" name="url" value={data.url} onChange={change} required placeholder="https://www.bbc.com" />
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

function ChannelForm({ initial, onSave, onCancel, isSubmitting, error, mediums, categories }) {
  const { t } = useTranslation()
  const [data, setData] = useState(initial || EMPTY_CHANNEL)

  const change = (e) => {
    const { name, value } = e.target
    setData({ ...data, [name]: name.endsWith('_id') ? Number(value) || '' : value })
  }
  const submit = (e) => {
    e.preventDefault()
    onSave(data)
  }

  return (
    <form className="source-form" onSubmit={submit}>
      <div className="field-grid">
        <label className="field">
          <span>{t('sources.medium')}</span>
          <select name="information_source_id" value={data.information_source_id} onChange={change} required>
            <option value="" disabled>—</option>
            {mediums.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>{t('sources.rss_url')}</span>
          <input
            type="url"
            name="url"
            value={data.url}
            onChange={change}
            required
            placeholder="https://feeds.bbci.co.uk/news/technology/rss.xml"
          />
        </label>
        <label className="field">
          <span>{t('sources.iptc_category')}</span>
          <select name="category_id" value={data.category_id} onChange={change} required>
            <option value="" disabled>{t('sources.select_category')}</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
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

export default function SourcesPage() {
  const { t } = useTranslation()
  const canEdit = true

  const [tab, setTab] = useState('channels')

  const [mediums, setMediums] = useState([])
  const [channels, setChannels] = useState([])
  const [categories, setCategories] = useState([])
  const [catalogSummary, setCatalogSummary] = useState(null)

  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    setStatus('loading')
    setError('')
    try {
      const [meds, cats, summary] = await Promise.all([
        getInformationSources(),
        getCategories(),
        getSourcesCatalogSummary(),
      ])
      setMediums(meds)
      setCategories(cats)
      setCatalogSummary(summary)

      const allChannels = []
      for (const m of meds) {
        const list = await getRssChannelsForSource(m.id)
        for (const ch of list) {
          allChannels.push({ ...ch, medium: m })
        }
      }
      setChannels(allChannels)
      setStatus('success')
    } catch (err) {
      setError(err.message || 'Error loading data')
      setStatus('error')
    }
  }, [])

  useEffect(() => { load() }, [load])

  const findMedium = (id) => mediums.find((m) => m.id === id)
  const findCategory = (id) => categories.find((c) => c.id === id)

  // ── Mediums handlers ──────────────────────────────────────────────

  const onSaveMedium = async (formData) => {
    setSubmitting(true); setFormError('')
    try {
      if (editing) {
        await updateInformationSource(editing.id, formData)
      } else {
        await createInformationSource(formData)
      }
      setShowForm(false); setEditing(null)
      await load()
    } catch (err) {
      setFormError(err.message || 'Error saving medium')
    } finally {
      setSubmitting(false)
    }
  }

  const onDeleteMedium = async (id) => {
    if (!window.confirm(t('sources.delete_confirm'))) return
    setBusyId(id)
    try {
      await deleteInformationSource(id)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  // ── Channels handlers ─────────────────────────────────────────────

  const onSaveChannel = async (formData) => {
    setSubmitting(true); setFormError('')
    try {
      const sourceId = Number(formData.information_source_id)
      const payload = {
        url: formData.url,
        category_id: Number(formData.category_id),
      }
      if (editing) {
        await updateRssChannel(editing.medium.id, editing.id, payload)
      } else {
        await createRssChannel(sourceId, payload)
      }
      setShowForm(false); setEditing(null)
      await load()
    } catch (err) {
      setFormError(err.message || 'Error saving channel')
    } finally {
      setSubmitting(false)
    }
  }

  const onDeleteChannel = async (channel) => {
    if (!window.confirm(t('sources.delete_confirm'))) return
    setBusyId(channel.id)
    try {
      await deleteRssChannel(channel.medium.id, channel.id)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const onToggleChannel = async (channel) => {
    setBusyId(channel.id)
    try {
      if (channel.is_active) {
        await deactivateRssChannel(channel.medium.id, channel.id)
      } else {
        await activateRssChannel(channel.medium.id, channel.id)
      }
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const openAdd = () => { setEditing(null); setShowForm(true); setFormError('') }
  const openEditMedium = (m) => { setEditing(m); setShowForm(true); setFormError('') }
  const openEditChannel = (ch) => { setEditing(ch); setShowForm(true); setFormError('') }
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
            <div><dt>{t('sources.initial_channels')}</dt><dd>{catalogSummary.total_channels}</dd></div>
            <div><dt>{t('sources.media_outlets')}</dt><dd>{catalogSummary.total_media_outlets}</dd></div>
            <div><dt>{t('sources.iptc_coverage')}</dt>
              <dd>{catalogSummary.iptc_categories_covered} / {catalogSummary.iptc_categories_total}</dd>
            </div>
            <div><dt>{t('sources.status')}</dt>
              <dd>{catalogSummary.covers_all_iptc_categories
                ? t('sources.all_covered')
                : t('sources.coverage_incomplete')}</dd>
            </div>
          </dl>
        </div>
      ) : null}

      <div className="sources-toolbar" style={{ display: 'flex', gap: '0.5rem' }}>
        <button
          type="button"
          className={tab === 'channels' ? 'primary-button' : 'secondary-button'}
          onClick={() => { setTab('channels'); cancelForm() }}
        >
          RSS Channels
        </button>
        <button
          type="button"
          className={tab === 'mediums' ? 'primary-button' : 'secondary-button'}
          onClick={() => { setTab('mediums'); cancelForm() }}
        >
          Information Sources
        </button>
        {canEdit && !showForm ? (
          <button type="button" className="primary-button" onClick={openAdd} style={{ marginLeft: 'auto' }}>
            {tab === 'channels' ? t('sources.add_source') : 'Add medium'}
          </button>
        ) : null}
      </div>

      {showForm ? (
        <div className="panel-card">
          <h2>{editing ? t('sources.edit_source') : t('sources.new_source')}</h2>
          {tab === 'channels' ? (
            <ChannelForm
              initial={editing ? {
                url: editing.url,
                category_id: editing.category_id,
                information_source_id: editing.information_source_id,
              } : null}
              onSave={onSaveChannel}
              onCancel={cancelForm}
              isSubmitting={submitting}
              error={formError}
              mediums={mediums}
              categories={categories}
            />
          ) : (
            <MediumForm
              initial={editing ? { name: editing.name, url: editing.url } : null}
              onSave={onSaveMedium}
              onCancel={cancelForm}
              isSubmitting={submitting}
              error={formError}
            />
          )}
        </div>
      ) : null}

      {status === 'loading' ? <p className="sources-feedback">{t('sources.loading')}</p> : null}
      {status === 'error' ? <p className="form-message form-message--error">{error}</p> : null}

      {status === 'success' && tab === 'channels' && channels.length === 0 ? (
        <div className="panel-card sources-empty"><p>{t('sources.empty')}</p></div>
      ) : null}

      {status === 'success' && tab === 'channels' && channels.length > 0 ? (
        <div className="sources-list">
          {channels.map((ch) => (
            <div key={ch.id} className="source-row">
              <div className="source-row__info">
                <strong className="source-row__name">{ch.medium?.name} — id #{ch.id}</strong>
                <a className="source-row__url" href={ch.url} target="_blank" rel="noreferrer noopener">
                  {ch.url}
                </a>
                <span className="source-row__url">
                  {t('sources.category_col')}: {findCategory(ch.category_id)?.name || ch.category_id}
                </span>
              </div>
              <span className={ch.is_active ? 'source-badge source-badge--active' : 'source-badge source-badge--inactive'}>
                {ch.is_active ? t('sources.active') : t('sources.inactive')}
              </span>
              {canEdit ? (
                <div className="source-row__actions">
                  <button type="button" className="secondary-button" onClick={() => onToggleChannel(ch)} disabled={busyId === ch.id}>
                    {ch.is_active ? t('sources.deactivate') : t('sources.activate')}
                  </button>
                  <button type="button" className="secondary-button" onClick={() => openEditChannel(ch)} disabled={busyId === ch.id}>
                    {t('sources.edit')}
                  </button>
                  <button type="button" className="danger-button" onClick={() => onDeleteChannel(ch)} disabled={busyId === ch.id}>
                    {t('sources.delete')}
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {status === 'success' && tab === 'mediums' && mediums.length > 0 ? (
        <div className="sources-list">
          {mediums.map((m) => (
            <div key={m.id} className="source-row">
              <div className="source-row__info">
                <strong className="source-row__name">{m.name}</strong>
                <a className="source-row__url" href={m.url} target="_blank" rel="noreferrer noopener">
                  {m.url}
                </a>
              </div>
              {canEdit ? (
                <div className="source-row__actions">
                  <button type="button" className="secondary-button" onClick={() => openEditMedium(m)} disabled={busyId === m.id}>
                    {t('sources.edit')}
                  </button>
                  <button type="button" className="danger-button" onClick={() => onDeleteMedium(m.id)} disabled={busyId === m.id}>
                    {t('sources.delete')}
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  )
}
