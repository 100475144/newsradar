import React, { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { getHealth } from '../../api/client'

function HealthBadge() {
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let ignore = false

    async function checkHealth() {
      try {
        await getHealth()

        if (!ignore) {
          setStatus('ok')
        }
      } catch (error) {
        if (!ignore) {
          setStatus('error')
        }
      }
    }

    checkHealth()

    return () => {
      ignore = true
    }
  }, [])

  const labels = {
    loading: 'Checking backend',
    ok: 'Backend online',
    error: 'Backend unavailable',
  }

  return (
    <div className={`health-pill health-pill--${status}`}>
      <span className="health-pill__dot" />
      <span>{labels[status]}</span>
    </div>
  )
}

export default function AuthLayout() {
  return (
    <div className="auth-layout">
      <section className="auth-layout__hero">
        <p className="eyebrow">NEWSRADAR</p>
        <h1>Sign in to continue.</h1>
        <p className="auth-layout__copy">
          Access your account or create a new one to enter the private area of the application.
        </p>

        <HealthBadge />
      </section>

      <section className="auth-layout__panel">
        <Outlet />
      </section>
    </div>
  )
}
