import React, { useCallback, useEffect, useState } from 'react'
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
import {
  getCategories,
  getInformationSources,
  getRssChannelsForSource,
} from '../api/sourcesApi'
import { request } from '../api/client'

const EMPTY_FORM = {
  name: '',
  keyword: '',
  descriptors: '',
  categories: [], // codes
  rss_channels_ids: [], // strings
  information_sources_ids: [], // strings
  cron_expression: '*/5 * * * *',
  notify_in_app: true,
  notify_email: false,
}

function parseDescriptors(raw) {
  if (!raw || !raw.trim()) return []
  return raw.split(',').map((k) => k.trim()).filter(Boolean)
}

function AlertForm({ initial, onSave, onCancel, isSubmitting, error, iptcCategories, mediums, channels }) {
  const { t } = useTranslation()
  const [form, setForm] = useState(initial || EMPTY_FORM)
  const [suggestions, setSuggestions] = useState([])
  const [suggestionsError, setSuggestionsError] = useState('')
  const [isSuggesting, setIsSuggesting] = useState(false)

  const change = (e) => {
    const { name, type, value, checked } = e.target
    setForm((s) => ({ ...s, [name]: type === 'checkbox' ? checked : value }))
  }

  const toggleInArray = (key, value) => {
    setForm((s) => {
      const has = s[key].includes(value)
      return { ...s, [key]: has ? s[key].filter((v) => v !== value) : [...s[key], value] }
    })
  }

  const submit = (e) => {
    e.preventDefault()
    const payload = {
      name: form.name.trim(),
      descriptors: parseDescriptors(form.descriptors),
      categories: form.categories.map((code) => {
        const cat = iptcCategories.find((c) => c.code === code)
        return { code, label: cat?.label || code }
      }),
      rss_channels_ids: form.rss_channels_ids.map(String),
      information_sources_ids: form.information_sources_ids.map(String),
      cron_expression: form.cron_expression,
      keyword: form.keyword.trim() || undefined,
      notify_in_app: form.notify_in_app,
      notify_email: form.notify_email,
    }
    onSave(payload)
  }

  const fetchSuggestions = async () => {
    const kw = form.keyword.trim()
    if (!kw) {
      setSuggestionsError(t('alerts.enter_keyword_first'))
      setSuggestions([])
      return
    }
    setIsSuggesting(true); setSuggestionsError('')
    try {
      const res = await getAlertSuggestions(kw)
      setSuggestions(res.suggestions || [])
    } catch (err) {
      setSuggestionsError(err.message || 'Unable to suggest right now.')
      setSuggestions([])
    } finally {
      setIsSuggesting(false)
    }
  }

  const applySuggestion = (term) => {
    const existing = parseDescriptors(form.descriptors)
    const lowered = existing.map((s) => s.toLowerCase())
    if (lowered.includes(term.toLowerCase())) {
      setForm((s) => ({ ...s, descriptors: existing.filter((x) => x.toLowerCase() !== term.toLowerCase()).join(', ') }))
    } else {
      setForm((s) => ({ ...s, descriptors: [...existing, term].slice(0, 10).join(', ') }))
    }
  }

  return (
    <form className="source-form" onSubmit={submit}>
      <div className="field-grid">
        <label className="field">
          <span>{t('alerts.alert_name')}</span>
          <input type="text" name="name" value={form.name} onChange={change} required maxLength={200} />
        </label>
        <label className="field">
          <span>{t('alerts.keyword')}</span>
          <input
            type="text"
            name="keyword"
            value={form.keyword}
            onChange={change}
            placeholder="ai"
          />
        </label>
        <label className="field">
          <span>{t('alerts.related_keywords')}</span>
          <input
            type="text"
            name="descriptors"
            value={form.descriptors}
            onChange={change}
            placeholder="machine learning, neural networks, deep learning"
          />
        </label>
        <label className="field">
          <span>cron_expression</span>
          <input type="text" name="cron_expression" value={form.cron_expression} onChange={change} required />
        </label>
      </div>

      <div className="alert-suggestions">
        <div className="alert-suggestions__toolbar">
          <button
            type="button"
            className="secondary-button"
            onClick={fetchSuggestions}
            disabled={isSubmitting || isSuggesting}
          >
            {isSuggesting ? t('alerts.generating') : t('alerts.recommend')}
          </button>
        </div>
        <p className="panel-card__text">{t('alerts.suggestions_info')}</p>
        {suggestionsError ? <p className="form-message form-message--error">{suggestionsError}</p> : null}
        {suggestions.length > 0 ? (
          <div className="alert-suggestions__list">
            {suggestions.map((term) => {
              const selected = parseDescriptors(form.descriptors).map((s) => s.toLowerCase()).includes(term.toLowerCase())
              return (
                <button
                  key={term}
                  type="button"
                  className={selected ? 'alert-suggestion-chip alert-suggestion-chip--active' : 'alert-suggestion-chip'}
                  onClick={() => applySuggestion(term)}
                >
                  {term}
                </button>
              )
            })}
          </div>
        ) : null}
      </div>

      <fieldset>
        <legend>{t('alerts.iptc_category')} ({t('alerts.select_one_or_more') || 'one or more'})</legend>
        <div className="alert-suggestions__list">
          {iptcCategories.map((cat) => {
            const selected = form.categories.includes(cat.code)
            return (
              <button
                key={cat.code}
                type="button"
                className={selected ? 'alert-suggestion-chip alert-suggestion-chip--active' : 'alert-suggestion-chip'}
                onClick={() => toggleInArray('categories', cat.code)}
              >
                {cat.label}
              </button>
            )
          })}
        </div>
      </fieldset>

      <fieldset>
        <legend>Information Sources (medios)</legend>
        <div className="alert-suggestions__list">
          {mediums.map((m) => {
            const idStr = String(m.id)
            const selected = form.information_sources_ids.includes(idStr)
            return (
              <button
                key={m.id}
                type="button"
                className={selected ? 'alert-suggestion-chip alert-suggestion-chip--active' : 'alert-suggestion-chip'}
                onClick={() => toggleInArray('information_sources_ids', idStr)}
              >
                {m.name}
              </button>
            )
          })}
        </div>
      </fieldset>

      <fieldset>
        <legend>RSS Channels</legend>
        <div className="alert-suggestions__list" style={{ maxHeight: 220, overflowY: 'auto' }}>
          {channels.map((ch) => {
            const idStr = String(ch.id)
            const selected = form.rss_channels_ids.includes(idStr)
            return (
              <button
                key={ch.id}
                type="button"
                className={selected ? 'alert-suggestion-chip alert-suggestion-chip--active' : 'alert-suggestion-chip'}
                onClick={() => toggleInArray('rss_channels_ids', idStr)}
                title={ch.url}
              >
                #{ch.id} {ch._medium?.name}
              </button>
            )
          })}
        </div>
      </fieldset>

      <div className="field-grid">
        <label className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
          <input type="checkbox" name="notify_in_app" checked={form.notify_in_app} onChange={change} />
          <span>{t('alerts.notify_in_app') || 'In-app notification'}</span>
        </label>
        <label className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
          <input type="checkbox" name="notify_email" checked={form.notify_email} onChange={change} />
          <span>{t('alerts.notify_email') || 'Email notification'}</span>
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

export default function AlertsPage() {
  const { t } = useTranslation()
  const canEdit = true

  const [items, setItems] = useState([])
  const [iptcCategories, setIptcCategories] = useState([])
  const [mediums, setMediums] = useState([])
  const [channels, setChannels] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    setStatus('loading'); setError('')
    try {
      const [alerts, iptc, meds, cats] = await Promise.all([
        getAlerts(),
        request('/alerts/categories'),
        getInformationSources(),
        getCategories(),
      ])
      // Cargar canales para todos los medios (necesarios para el form)
      const allChannels = []
      for (const m of meds) {
        const list = await getRssChannelsForSource(m.id)
        for (const ch of list) {
          allChannels.push({ ...ch, _medium: m, _category: cats.find((c) => c.id === ch.category_id) })
        }
      }
      setItems(alerts)
      setIptcCategories(iptc)
      setMediums(meds)
      setChannels(allChannels)
      setStatus('success')
    } catch (err) {
      setError(err.message || 'Error loading data')
      setStatus('error')
    }
  }, [])

  useEffect(() => { load() }, [load])

  const onSave = async (payload) => {
    setSubmitting(true); setFormError('')
    try {
      if (editing) {
        await updateAlert(editing.user_id, editing.id, payload)
      } else {
        await createAlert(payload)
      }
      setShowForm(false); setEditing(null)
      await load()
    } catch (err) {
      setFormError(err.message || 'Error saving alert')
    } finally {
      setSubmitting(false)
    }
  }

  const onDelete = async (alert) => {
    if (!window.confirm(t('alerts.delete_confirm') || '¿Eliminar alerta?')) return
    setBusyId(alert.id)
    try {
      await deleteAlert(alert.user_id, alert.id)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const onToggle = async (alert) => {
    setBusyId(alert.id)
    try {
      if (alert.is_active) {
        await deactivateAlert(alert.user_id, alert.id)
      } else {
        await activateAlert(alert.user_id, alert.id)
      }
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const openAdd = () => { setEditing(null); setShowForm(true); setFormError('') }
  const openEdit = (alert) => {
    setEditing({
      ...alert,
      // Hidratar form a partir de la respuesta canónica
      _form: {
        name: alert.name,
        keyword: alert.keyword || '',
        descriptors: (alert.descriptors || []).join(', '),
        categories: (alert.categories || []).map((c) => c.code),
        rss_channels_ids: (alert.rss_channels_ids || []).map(String),
        information_sources_ids: (alert.information_sources_ids || []).map(String),
        cron_expression: alert.cron_expression,
        notify_in_app: alert.notify_in_app,
        notify_email: alert.notify_email,
      },
    })
    setShowForm(true); setFormError('')
  }
  const cancelForm = () => { setShowForm(false); setEditing(null); setFormError('') }

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">{t('alerts.eyebrow') || 'Alerts'}</p>
        <h1>{t('alerts.title') || 'Alertas'}</h1>
        <p>{t('alerts.subtitle') || 'Define palabras clave y filtros para recibir notificaciones'}</p>
      </div>

      <div className="sources-toolbar">
        {canEdit && !showForm ? (
          <button type="button" className="primary-button" onClick={openAdd}>
            {t('alerts.add') || 'Nueva alerta'}
          </button>
        ) : null}
      </div>

      {showForm ? (
        <div className="panel-card">
          <h2>{editing ? (t('alerts.edit') || 'Editar alerta') : (t('alerts.new') || 'Nueva alerta')}</h2>
          <AlertForm
            initial={editing?._form || null}
            onSave={onSave}
            onCancel={cancelForm}
            isSubmitting={submitting}
            error={formError}
            iptcCategories={iptcCategories}
            mediums={mediums}
            channels={channels}
          />
        </div>
      ) : null}

      {status === 'loading' ? <p className="sources-feedback">{t('sources.loading')}</p> : null}
      {status === 'error' ? <p className="form-message form-message--error">{error}</p> : null}

      {status === 'success' && items.length === 0 ? (
        <div className="panel-card sources-empty"><p>{t('alerts.empty') || 'No tienes alertas aún.'}</p></div>
      ) : null}

      {status === 'success' && items.length > 0 ? (
        <div className="sources-list">
          {items.map((alert) => (
            <div key={alert.id} className="source-row">
              <div className="source-row__info">
                <strong className="source-row__name">{alert.name}</strong>
                {alert.keyword ? (
                  <span className="source-row__url">keyword: {alert.keyword}</span>
                ) : null}
                {alert.descriptors?.length ? (
                  <span className="source-row__url">descriptors: {alert.descriptors.join(', ')}</span>
                ) : null}
                {alert.categories?.length ? (
                  <span className="source-row__url">
                    categories: {alert.categories.map((c) => c.label).join(', ')}
                  </span>
                ) : null}
                {alert.information_sources_ids?.length ? (
                  <span className="source-row__url">
                    media: {alert.information_sources_ids.length} selected
                  </span>
                ) : null}
                {alert.rss_channels_ids?.length ? (
                  <span className="source-row__url">
                    channels: {alert.rss_channels_ids.length} selected
                  </span>
                ) : null}
                <span className="source-row__url">cron: {alert.cron_expression}</span>
              </div>
              <span className={alert.is_active ? 'source-badge source-badge--active' : 'source-badge source-badge--inactive'}>
                {alert.is_active ? (t('sources.active') || 'Activo') : (t('sources.inactive') || 'Inactivo')}
              </span>
              {canEdit ? (
                <div className="source-row__actions">
                  <button type="button" className="secondary-button" onClick={() => onToggle(alert)} disabled={busyId === alert.id}>
                    {alert.is_active ? (t('sources.deactivate') || 'Desactivar') : (t('sources.activate') || 'Activar')}
                  </button>
                  <button type="button" className="secondary-button" onClick={() => openEdit(alert)} disabled={busyId === alert.id}>
                    {t('sources.edit') || 'Editar'}
                  </button>
                  <button type="button" className="danger-button" onClick={() => onDelete(alert)} disabled={busyId === alert.id}>
                    {t('sources.delete') || 'Eliminar'}
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
