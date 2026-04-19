import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { resendVerification } from '../api/authApi'
import { useAuth } from '../context/AuthContext'

const INITIAL_FORM = {
  email: '',
  password: '',
}

export default function LoginPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState(() => location.state?.message || '')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isResendingVerification, setIsResendingVerification] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({
      ...current,
      [name]: value,
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setNotice('')
    setIsSubmitting(true)

    try {
      await login(formData)
      navigate('/dashboard', { replace: true })
    } catch (requestError) {
      setError(requestError.message || 'Unable to sign in.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const canResendVerification =
    Boolean(formData.email) && error.toLowerCase().includes('not verified')

  const handleResendVerification = async () => {
    setError('')
    setNotice('')
    setIsResendingVerification(true)

    try {
      const response = await resendVerification(formData.email)
      setNotice(response.message || 'Verification email sent. Please check your inbox.')
    } catch (requestError) {
      setError(requestError.message || 'Unable to resend verification email.')
    } finally {
      setIsResendingVerification(false)
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-card__header">
        <p className="eyebrow">Welcome back</p>
        <h2>Sign in to your account</h2>
        <p>Use your registered email and password after verifying your email address.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Email</span>
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
          <span>Password</span>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
            autoComplete="current-password"
            required
          />
        </label>

        {notice ? <p className="form-message form-message--success">{notice}</p> : null}
        {error ? <p className="form-message form-message--error">{error}</p> : null}

        <button
          type="submit"
          className="primary-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>

        {canResendVerification ? (
          <button
            type="button"
            className="secondary-button"
            onClick={handleResendVerification}
            disabled={isResendingVerification}
          >
            {isResendingVerification
              ? 'Resending verification email...'
              : 'Resend verification email'}
          </button>
        ) : null}
      </form>

      <p className="auth-card__footer">
        No account yet? <Link to="/register">Create one now</Link>.
      </p>
    </div>
  )
}
