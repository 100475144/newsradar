import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { deleteUserAccount, updateUserProfile } from '../api/authApi'
import { useAuth } from '../context/AuthContext'

const EMPTY_FORM = {
  first_name: '',
  last_name: '',
  organization: '',
  email: '',
  password: '',
}

export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth()
  const { t } = useTranslation()
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')

  useEffect(() => {
    setFormData({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      organization: user?.organization || '',
      email: user?.email || '',
      password: '',
    })
  }, [user])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus('saving')
    setMessage('')

    const payload = {
      first_name: formData.first_name.trim(),
      last_name: formData.last_name.trim(),
      organization: formData.organization.trim(),
      email: formData.email.trim(),
    }

    if (formData.password.trim()) {
      payload.password = formData.password.trim()
    }

    try {
      await updateUserProfile(user.id, payload)
      await refreshUser()
      setFormData((current) => ({ ...current, password: '' }))
      setStatus('success')
      setMessage(t('profile.saved'))
    } catch (error) {
      setStatus('error')
      setMessage(error.message || t('profile.save_error'))
    }
  }

  const handleDeleteAccount = async () => {
    if (!globalThis.confirm(t('profile.delete_confirm'))) return
    setStatus('deleting')
    setMessage('')

    try {
      await deleteUserAccount(user.id)
      logout()
    } catch (error) {
      setStatus('error')
      setMessage(error.message || t('profile.delete_error'))
    }
  }

  return (
    <section className="sources-page">
      <div className="hero-card">
        <p className="eyebrow">{t('profile.eyebrow')}</p>
        <h1>{t('profile.title')}</h1>
        <p>{t('profile.subtitle')}</p>
      </div>

      <div className="panel-card">
        <h2>{t('profile.personal_data')}</h2>
        <form className="source-form" onSubmit={handleSubmit}>
          <div className="field-grid">
            <label className="field">
              <span>{t('profile.first_name')}</span>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                maxLength={120}
                required
              />
            </label>

            <label className="field">
              <span>{t('profile.last_name')}</span>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                maxLength={120}
                required
              />
            </label>
          </div>

          <label className="field">
            <span>{t('profile.organization')}</span>
            <input
              type="text"
              name="organization"
              value={formData.organization}
              onChange={handleChange}
              maxLength={180}
              required
            />
          </label>

          <label className="field">
            <span>{t('profile.email')}</span>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </label>

          <label className="field">
            <span>{t('profile.new_password')}</span>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              minLength={8}
              maxLength={128}
              placeholder={t('profile.password_placeholder')}
              autoComplete="new-password"
            />
          </label>

          {message ? (
            <p
              className={
                status === 'error'
                  ? 'form-message form-message--error'
                  : 'form-message form-message--success'
              }
            >
              {message}
            </p>
          ) : null}

          <div className="source-form__actions">
            <button type="submit" className="primary-button" disabled={status === 'saving'}>
              {status === 'saving' ? t('profile.saving') : t('profile.save')}
            </button>
          </div>
        </form>
      </div>

      <div className="panel-card">
        <h2>{t('profile.danger_zone')}</h2>
        <p className="panel-card__text">{t('profile.delete_help')}</p>
        <button
          type="button"
          className="danger-button"
          onClick={handleDeleteAccount}
          disabled={status === 'deleting'}
        >
          {status === 'deleting' ? t('profile.deleting') : t('profile.delete_account')}
        </button>
      </div>
    </section>
  )
}
