import React from 'react'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { AuthProvider } from '../context/AuthContext'

/**
 * Envuelve cualquier componente con los providers necesarios para que
 * renderice sin errores en los smoke tests:
 * - MemoryRouter (Link, useNavigate, useLocation)
 * - AuthProvider (useAuth)
 */
export function renderWithProviders(ui, { route = '/' } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>,
  )
}
