import React from 'react'
import { describe, it, expect } from 'vitest'

import AlertsPage from './AlertsPage'
import { renderWithProviders } from '../test/render'

describe('AlertsPage', () => {
  it('renders without crashing', () => {
    // Solo nos aseguramos de que la página se monta correctamente con todos
    // los providers (Router + Auth + i18n). Las llamadas a la API están
    // mockeadas en setup.js para devolver listas vacías.
    const { container } = renderWithProviders(<AlertsPage />)
    expect(container).toBeTruthy()
  })

  it('shows the page hero card', () => {
    renderWithProviders(<AlertsPage />)
    // El hero usa `t('alerts.title')` o un fallback. Con el mock, t devuelve
    // la propia key, que aparece como texto en el DOM.
    const headings = document.querySelectorAll('h1')
    expect(headings.length).toBeGreaterThanOrEqual(1)
  })
})
