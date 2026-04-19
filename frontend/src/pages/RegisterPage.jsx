import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
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
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

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
        <p className="eyebrow">New workspace</p>
        <h2>Create your account</h2>
        <p>
          We will send you a verification email before you can sign in to the private workspace.
        </p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="field-grid">
          <label className="field">
            <span>First name</span>
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
            <span>Last name</span>
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
          <span>Organization</span>
          <input
            type="text"
            name="organization"
            value={formData.organization}
            onChange={handleChange}
            placeholder="Optional"
            autoComplete="organization"
          />
        </label>

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
            placeholder="Minimum 8 characters"
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>

        {error ? <p className="form-message form-message--error">{error}</p> : null}

        <button
          type="submit"
          className="primary-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p className="auth-card__footer">
        Already registered? <Link to="/login">Sign in here</Link>.
      </p>
    </div>
  )
}
