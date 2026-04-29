import React from 'react'
import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'

import LoginPage from './LoginPage'
import { renderWithProviders } from '../test/render'

describe('LoginPage', () => {
  it('renders the email and password inputs', () => {
    renderWithProviders(<LoginPage />)

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

  it('uses i18n keys for visible texts', () => {
    renderWithProviders(<LoginPage />)
    // Con el mock de i18n, t("…") devuelve la propia key, así que debe haber
    // varios textos que empiezan por "login.". Usamos queryAllByText (varios
    // matches son esperables) y comprobamos que hay al menos uno.
    const matches = screen.queryAllByText(/^login\./i)
    expect(matches.length).toBeGreaterThan(0)
  })
})
