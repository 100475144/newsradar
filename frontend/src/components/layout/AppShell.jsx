import React from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

function buildFullName(user) {
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ')
}

export default function AppShell() {
  const { user, logout } = useAuth()

  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar">
        <p className="eyebrow">NEWSRADAR</p>
        <h1>Dashboard</h1>
        <p className="app-shell__copy">
          Your session is active.
        </p>

        <nav className="app-shell__nav" aria-label="Main navigation">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/sources"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            Sources
          </NavLink>
          <NavLink
            to="/alerts"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            Alerts
          </NavLink>
        </nav>

        <div className="profile-card">
          <span className="profile-card__label">Signed in as</span>
          <strong>{buildFullName(user) || user?.email}</strong>
          <span>{user?.email}</span>
          <span>{user?.organization || 'No organization assigned yet'}</span>
        </div>
      </aside>

      <main className="app-shell__content">
        <header className="app-shell__header">
          <div>
            <p className="eyebrow">Private area</p>
            <h2>Welcome back</h2>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={logout}
          >
            Log out
          </button>
        </header>

        <Outlet />
      </main>
    </div>
  )
}
