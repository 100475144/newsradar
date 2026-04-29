import React from 'react'
import { describe, it, expect } from 'vitest'

import NewsPage from './NewsPage'
import { renderWithProviders } from '../test/render'

describe('NewsPage', () => {
  it('renders without crashing', () => {
    const { container } = renderWithProviders(<NewsPage />)
    expect(container).toBeTruthy()
  })

  it('renders a category filter input', () => {
    renderWithProviders(<NewsPage />)
    // NewsPage filtra categorías con un <input type="text">. Comprobamos que
    // existe al menos un input de texto en el toolbar.
    const inputs = document.querySelectorAll('input[type="text"]')
    expect(inputs.length).toBeGreaterThan(0)
  })
})
