import React, { useEffect, useState } from 'react'
import { getHealth } from '../api/client'
import { useAuth } from '../context/AuthContext'

function formatTimestamp(value) {
  if (!value) {
    return 'Not available'
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [health, setHealth] = useState({
    status: 'loading',
    data: null,
    error: '',
  })

  useEffect(() => {
    let ignore = false

    async function loadHealth() {
      try {
        const data = await getHealth()

        if (!ignore) {
          setHealth({
            status: 'success',
            data,
            error: '',
          })
        }
      } catch (error) {
        if (!ignore) {
          setHealth({
            status: 'error',
            data: null,
            error: error.message,
          })
        }
      }
    }

    loadHealth()

    return () => {
      ignore = true
    }
  }, [])

  return (
    <section className="dashboard-page">
      <div className="hero-card">
        <p className="eyebrow">Session</p>
        <h1>You are signed in.</h1>
        <p>
          This is the protected area that is only available after a valid login.
        </p>
      </div>

      <div className="dashboard-grid">
        <article className="panel-card">
          <h2>Current user</h2>
          <dl className="detail-list">
            <div>
              <dt>Name</dt>
              <dd>{[user?.first_name, user?.last_name].filter(Boolean).join(' ') || 'Unknown user'}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user?.email || 'Not available'}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{user?.role || 'reader'}</dd>
            </div>
            <div>
              <dt>Organization</dt>
              <dd>{user?.organization || 'Not assigned'}</dd>
            </div>
            <div>
              <dt>Created at</dt>
              <dd>{formatTimestamp(user?.created_at)}</dd>
            </div>
          </dl>
        </article>

        <article className="panel-card">
          <h2>Backend status</h2>
          {health.status === 'loading' ? <p>Checking API health...</p> : null}
          {health.status === 'success' ? (
            <div className="status-stack">
              <span className="status-pill status-pill--ok">Backend reachable</span>
              <pre>{JSON.stringify(health.data, null, 2)}</pre>
            </div>
          ) : null}
          {health.status === 'error' ? (
            <div className="status-stack">
              <span className="status-pill status-pill--error">Connection issue</span>
              <p>{health.error}</p>
            </div>
          ) : null}
        </article>

        <article className="panel-card">
          <h2>What this page confirms</h2>
          <p className="panel-card__text">
            Route protection is working and the current authenticated user has been loaded correctly.
          </p>
        </article>
      </div>
    </section>
  )
}
