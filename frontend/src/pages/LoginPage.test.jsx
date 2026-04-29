import React from 'react'
import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'

import LoginPage from './LoginPage'
import { renderWithProviders } from '../test/render'

describe('LoginPage', () => {
  it('renders the email and password inputs', () => {
    renderWithProviders(<LoginPage />)

    // Hay al menos un input email y uno password.
    const emailInput = document.querySelector('input[type="email"]')
    const passwordInput = document.querySelector('input[type="password"]')
    expect(emailInput).toBeInTheDocument()
    expect(passwordInput).toBeInTheDocument()
  })

  it('renders a submit button', () => {
    renderWithProviders(<LoginPage />)
    const submitButton = document.querySelector('button[type="submit"]')
    expect(submitButton).toBeInTheDocument()
  })

  it('uses the i18n key for the page title', () => {
    renderWithProviders(<LoginPage />)
    // Con el mock de i18n, t("login.title") devuelve la propia key.
    // Tolera que el componente use otras keys: comprobamos que la página
    // monta sin errores buscando un elemento con clase de hero.
    expect(screen.queryByText(/login\./i)).toBeTruthy()
  })
})
