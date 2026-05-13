import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { verifyEmail } from '../api/authApi'

export default function VerifyEmailPage() {
  const token = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('token') || ''
  }, [])
  const [status, setStatus] = useState(() => (token ? 'loading' : 'error'))
  const [message, setMessage] = useState(() =>
    token ? '' : 'This verification link is invalid or incomplete.',
  )
  const calledRef = useRef(false)

  useEffect(() => {
    if (!token || calledRef.current) {
      return
    }
    calledRef.current = true

    async function confirmEmail() {
      try {
        const response = await verifyEmail(token)

        setStatus('success')
        setMessage(
          response.message || 'Email verified successfully. You can now sign in.',
        )
      } catch (error) {
        setStatus('error')
        setMessage(error.message || 'Unable to verify this email link.')
      }
    }

    confirmEmail()
  }, [token])

  return (
    <div className="auth-card">
      <div className="auth-card__header">
        <p className="eyebrow">Email Verification</p>
        <h2>Confirming your account</h2>
        <p>
          We are validating the verification link so you can safely access the
          private workspace.
        </p>
      </div>

      {status === 'loading' ? (
        <p className="form-message form-message--success">
          Verifying your email address...
        </p>
      ) : null}

      {status === 'success' ? (
        <p className="form-message form-message--success">{message}</p>
      ) : null}

      {status === 'error' ? (
        <p className="form-message form-message--error">{message}</p>
      ) : null}

      <div className="source-form__actions" style={{ marginTop: '1rem' }}>
        <Link className="primary-button" to="/login">
          Go to sign in
        </Link>
        <Link className="secondary-button" to="/register">
          Create another account
        </Link>
      </div>
    </div>
  )
}
