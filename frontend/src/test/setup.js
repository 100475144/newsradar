// Setup global para los smoke tests con vitest + Testing Library.
import '@testing-library/jest-dom/vitest'

// react-i18next requiere un provider; configuramos un mock mínimo que
// devuelve la key sin traducir, así no necesitamos cargar locales en cada
// test y los asserts se hacen sobre la key (e.g. "alerts.add").
import { vi } from 'vitest'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key,
    i18n: { changeLanguage: () => Promise.resolve() },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
  Trans: ({ children }) => children,
}))

// fetch global por si alguna página dispara peticiones al cargar.
// Los tests no asertan respuestas; devolvemos siempre un payload vacío.
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve([]),
    text: () => Promise.resolve(''),
    headers: { get: () => 'application/json' },
  }),
)
