import React, { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { resetPassword } from '../api/authApi'

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const token = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('token') || ''
  }, [])
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState(token ? 'idle' : 'error')
  const [message, setMessage] = useState(token ? '' : t('reset_password.invalid_link'))

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus('saving')
    setMessage('')

    try {
      const response = await resetPassword({ token, password })
      navigate('/login', {
        replace: true,
        state: {
          message: t('reset_password.saved'),
        },
      })
    } catch (error) {
      setStatus('error')
      setMessage(error.message || t('reset_password.error'))
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-card__header">
        <p className="eyebrow">{t('reset_password.eyebrow')}</p>
        <h2>{t('reset_password.title')}</h2>
        <p>{t('reset_password.subtitle')}</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>{t('reset_password.password')}</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={t('reset_password.password_placeholder')}
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            disabled={!token}
            required
          />
        </label>

        {message ? <p className="form-message form-message--error">{message}</p> : null}

        <button
          type="submit"
          className="primary-button"
          disabled={!token || status === 'saving'}
        >
          {status === 'saving' ? t('reset_password.saving') : t('reset_password.save')}
        </button>
      </form>

      <p className="auth-card__footer">
        <Link to="/login">{t('reset_password.back_to_login')}</Link>
      </p>
    </div>
  )
}
