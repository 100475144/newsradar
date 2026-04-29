import React from 'react'
import { describe, it, expect } from 'vitest'

import NewsPage from './NewsPage'
import { renderWithProviders } from '../test/render'

describe('NewsPage', () => {
  it('renders without crashing', () => {
    const { container } = renderWithProviders(<NewsPage />)
    expect(container).toBeTruthy()
  })

  it('renders a category filter <select>', async () => {
    renderWithProviders(<NewsPage />)
    // Esperamos un select para filtrar por categoría IPTC.
    const select = document.querySelector('select')
    expect(select).toBeInTheDocument()
  })
})
