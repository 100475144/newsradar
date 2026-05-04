import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { resetPassword } from '../api/authApi'
import RecoveryCard from '../components/auth/RecoveryCard'

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const token = useMemo(() => {
    const params = new URLSearchParams(globalThis.location.search)
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
      await resetPassword({ token, password })
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
    <RecoveryCard
      eyebrow={t('reset_password.eyebrow')}
      title={t('reset_password.title')}
      subtitle={t('reset_password.subtitle')}
      message={message}
      submitLabel={status === 'saving' ? t('reset_password.saving') : t('reset_password.save')}
      isSubmitting={status === 'saving'}
      isDisabled={!token}
      onSubmit={handleSubmit}
      backLabel={t('reset_password.back_to_login')}
    >
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
    </RecoveryCard>
  )
}
