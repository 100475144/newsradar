import React from 'react'
import { Link } from 'react-router-dom'

export default function RecoveryCard({
  eyebrow,
  title,
  subtitle,
  children,
  message,
  messageType = 'error',
  submitLabel,
  isSubmitting,
  isDisabled = false,
  onSubmit,
  backLabel,
}) {
  return (
    <div className="auth-card">
      <div className="auth-card__header">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>

      <form className="auth-form" onSubmit={onSubmit}>
        {children}

        {message ? (
          <p className={`form-message form-message--${messageType}`}>
            {message}
          </p>
        ) : null}

        <button
          type="submit"
          className="primary-button"
          disabled={isDisabled || isSubmitting}
        >
          {submitLabel}
        </button>
      </form>

      <p className="auth-card__footer">
        <Link to="/login">{backLabel}</Link>
      </p>
    </div>
  )
}
