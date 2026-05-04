import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  clearStoredToken,
  getStoredToken,
  setStoredToken,
} from '../api/client'
import { getCurrentUser, loginUser, registerUser } from '../api/authApi'

const AuthContext = createContext(null)

function persistSession(authPayload) {
  setStoredToken(authPayload.access_token)
  return authPayload.user
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken())
  const [user, setUser] = useState(null)
  const [isBootstrapping, setIsBootstrapping] = useState(() => Boolean(getStoredToken()))

  useEffect(() => {
    let ignore = false

    async function restoreSession() {
      if (!token) {
        setUser(null)
        setIsBootstrapping(false)
        return
      }

      setIsBootstrapping(true)

      try {
        const currentUser = await getCurrentUser(token)

        if (!ignore) {
          setUser(currentUser)
        }
      } catch (error) {
        if (!ignore) {
          clearStoredToken()
          setToken(null)
          setUser(null)
        }
      } finally {
        if (!ignore) {
          setIsBootstrapping(false)
        }
      }
    }

    restoreSession()

    return () => {
      ignore = true
    }
  }, [token])

  const login = async (credentials) => {
    const authPayload = await loginUser(credentials)
    const authenticatedUser = persistSession(authPayload)

    setToken(authPayload.access_token)
    setUser(authenticatedUser)

    return authenticatedUser
  }

  const register = async (payload) => {
    return registerUser(payload)
  }

  const refreshUser = async () => {
    if (!token) return null
    const currentUser = await getCurrentUser(token)
    setUser(currentUser)
    return currentUser
  }

  const logout = () => {
    clearStoredToken()
    setToken(null)
    setUser(null)
  }

  const value = {
    token,
    user,
    isAuthenticated: Boolean(token && user),
    isBootstrapping,
    login,
    register,
    refreshUser,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider.')
  }

  return context
}
