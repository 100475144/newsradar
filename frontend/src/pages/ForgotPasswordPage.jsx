import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { requestPasswordReset } from '../api/authApi'

export default function ForgotPasswordPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus('sending')
    setMessage('')

    try {
      await requestPasswordReset(email)
      setStatus('success')
      setMessage(t('forgot_password.sent'))
    } catch (error) {
      setStatus('error')
      setMessage(error.message || t('forgot_password.error'))
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-card__header">
        <p className="eyebrow">{t('forgot_password.eyebrow')}</p>
        <h2>{t('forgot_password.title')}</h2>
        <p>{t('forgot_password.subtitle')}</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>{t('forgot_password.email')}</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="team@newsradar.dev"
            autoComplete="email"
            required
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

        <button type="submit" className="primary-button" disabled={status === 'sending'}>
          {status === 'sending' ? t('forgot_password.sending') : t('forgot_password.send')}
        </button>
      </form>

      <p className="auth-card__footer">
        <Link to="/login">{t('forgot_password.back_to_login')}</Link>
      </p>
    </div>
  )
}
