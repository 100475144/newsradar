import React from 'react'
import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom'
import AuthLayout from '../components/layout/AuthLayout'
import AppShell from '../components/layout/AppShell'
import { useAuth } from '../context/AuthContext'
import DashboardPage from '../pages/DashboardPage'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'
import VerifyEmailPage from '../pages/VerifyEmailPage'
import SourcesPage from '../pages/SourcesPage'
import AlertsPage from '../pages/AlertsPage'
import NewsPage from '../pages/NewsPage'
import NotificationsPage from '../pages/NotificationsPage'
import ProfilePage from '../pages/ProfilePage'

function SessionLoader() {
  return (
    <div className="session-loader">
      <div className="session-loader__card">
        <p className="eyebrow">NEWSRADAR</p>
        <h1>Restoring your session</h1>
        <p>Checking the saved token and syncing your profile.</p>
      </div>
    </div>
  )
}

function ProtectedRoute() {
  const { isAuthenticated, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return <SessionLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

function PublicRoute() {
  const { isAuthenticated, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return <SessionLoader />
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}

function RootRedirect() {
  const { isAuthenticated, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return <SessionLoader />
  }

  return (
    <Navigate
      to={isAuthenticated ? '/dashboard' : '/login'}
      replace
    />
  )
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />

        <Route element={<PublicRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
        </Route>

        <Route element={<AuthLayout />}>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/news" element={<NewsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
