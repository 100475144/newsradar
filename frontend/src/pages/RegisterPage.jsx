import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'

const INITIAL_FORM = {
  first_name: '',
  last_name: '',
  organization: '',
  email: '',
  password: '',
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const { t } = useTranslation()
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const response = await register(formData)
      navigate('/login', {
        replace: true,
        state: {
          message:
            response.message ||
            'Account created successfully. Check your email to verify your account before signing in.',
        },
      })
    } catch (requestError) {
      setError(requestError.message || 'Unable to create the account.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-card__header">
        <p className="eyebrow">{t('register.eyebrow')}</p>
        <h2>{t('register.title')}</h2>
        <p>{t('register.subtitle')}</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="field-grid">
          <label className="field">
            <span>{t('register.first_name')}</span>
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="Alicia"
              autoComplete="given-name"
              required
            />
          </label>

          <label className="field">
            <span>{t('register.last_name')}</span>
            <input
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="Martin"
              autoComplete="family-name"
              required
            />
          </label>
        </div>

        <label className="field">
          <span>{t('register.organization')}</span>
          <input
            type="text"
            name="organization"
            value={formData.organization}
            onChange={handleChange}
            placeholder={t('register.organization_placeholder')}
            autoComplete="organization"
          />
        </label>

        <label className="field">
          <span>{t('register.email')}</span>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="team@newsradar.dev"
            autoComplete="email"
            required
          />
        </label>

        <label className="field">
          <span>{t('register.password')}</span>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder={t('register.password_placeholder')}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>

        {error ? <p className="form-message form-message--error">{error}</p> : null}

        <button type="submit" className="primary-button" disabled={isSubmitting}>
          {isSubmitting ? t('register.creating') : t('register.create')}
        </button>
      </form>

      <p className="auth-card__footer">
        {t('register.already_registered')} <Link to="/login">{t('register.sign_in_here')}</Link>.
      </p>
    </div>
  )
}
