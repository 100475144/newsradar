import React from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'

function buildFullName(user) {
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ')
}

function LanguageToggle() {
  const { i18n } = useTranslation()
  const current = i18n.language?.startsWith('es') ? 'es' : 'en'

  return (
    <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.75rem' }}>
      <button
        type="button"
        onClick={() => i18n.changeLanguage('es')}
        style={{
          background: current === 'es' ? 'rgba(255,255,255,0.18)' : 'transparent',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '6px',
          color: 'rgba(237,246,255,0.9)',
          cursor: 'pointer',
          fontSize: '0.78rem',
          fontWeight: current === 'es' ? 700 : 400,
          padding: '0.2rem 0.5rem',
        }}
      >
        🇪🇸 ES
      </button>
      <button
        type="button"
        onClick={() => i18n.changeLanguage('en')}
        style={{
          background: current === 'en' ? 'rgba(255,255,255,0.18)' : 'transparent',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: '6px',
          color: 'rgba(237,246,255,0.9)',
          cursor: 'pointer',
          fontSize: '0.78rem',
          fontWeight: current === 'en' ? 700 : 400,
          padding: '0.2rem 0.5rem',
        }}
      >
        🇬🇧 EN
      </button>
    </div>
  )
}

export default function AppShell() {
  const { user, logout } = useAuth()
  const { t } = useTranslation()

  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar">
        <p className="eyebrow">{t('sidebar.brand')}</p>
        <h1>{t('sidebar.title')}</h1>
        <p className="app-shell__copy">
          {t('sidebar.session_active')}
        </p>

        <nav className="app-shell__nav" aria-label="Main navigation">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            {t('sidebar.nav.dashboard')}
          </NavLink>
          <NavLink
            to="/sources"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            {t('sidebar.nav.sources')}
          </NavLink>
          <NavLink
            to="/alerts"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            {t('sidebar.nav.alerts')}
          </NavLink>
          <NavLink
            to="/news"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            {t('sidebar.nav.news')}
          </NavLink>
          <NavLink
            to="/notifications"
            className={({ isActive }) =>
              isActive ? 'nav-link nav-link--active' : 'nav-link'
            }
          >
            {t('sidebar.nav.notifications')}
          </NavLink>
        </nav>

        <div className="profile-card">
          <span className="profile-card__label">{t('sidebar.signed_in_as')}</span>
          <strong>{buildFullName(user) || user?.email}</strong>
          <span>{user?.email}</span>
          <span>{user?.organization || t('sidebar.no_org')}</span>
          <span style={{
            display: 'inline-block',
            marginTop: '0.4rem',
            padding: '0.2rem 0.6rem',
            borderRadius: '999px',
            fontSize: '0.72rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            background: user?.role === 'admin' ? 'rgba(255,200,80,0.18)' : 'rgba(237,246,255,0.12)',
            color: user?.role === 'admin' ? '#ffc850' : 'rgba(237,246,255,0.75)',
            border: user?.role === 'admin' ? '1px solid rgba(255,200,80,0.4)' : '1px solid rgba(237,246,255,0.2)',
          }}>
            {user?.role}
          </span>
          <LanguageToggle />
        </div>
      </aside>

      <main className="app-shell__content">
        <header className="app-shell__header">
          <div>
            <p className="eyebrow">{t('sidebar.private_area')}</p>
            <h2>{t('sidebar.welcome_back')}</h2>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={logout}
          >
            {t('sidebar.logout')}
          </button>
        </header>

        <Outlet />
      </main>
    </div>
  )
}
