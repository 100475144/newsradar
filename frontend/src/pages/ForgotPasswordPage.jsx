import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { requestPasswordReset } from '../api/authApi'
import RecoveryCard from '../components/auth/RecoveryCard'

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
    <RecoveryCard
      eyebrow={t('forgot_password.eyebrow')}
      title={t('forgot_password.title')}
      subtitle={t('forgot_password.subtitle')}
      message={message}
      messageType={status === 'error' ? 'error' : 'success'}
      submitLabel={status === 'sending' ? t('forgot_password.sending') : t('forgot_password.send')}
      isSubmitting={status === 'sending'}
      onSubmit={handleSubmit}
      backLabel={t('forgot_password.back_to_login')}
    >
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
    </RecoveryCard>
  )
}
