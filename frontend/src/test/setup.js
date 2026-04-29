// Setup global para los smoke tests con vitest + Testing Library.
import '@testing-library/jest-dom/vitest'
import { vi, beforeEach } from 'vitest'

// react-i18next requiere un provider; configuramos un mock mínimo que
// devuelve la key sin traducir, así no necesitamos cargar locales en cada
// test y los asserts se hacen sobre la key (e.g. "alerts.add").
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

// Algunas builds de jsdom no exponen Storage por defecto al `window`. Lo
// reimplementamos en memoria para que ``client.js::getStoredToken`` pueda
// montar AuthProvider sin crashear.
function createMemoryStorage() {
  const store = new Map()
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
    key: (i) => Array.from(store.keys())[i] ?? null,
    get length() { return store.size },
  }
}

if (typeof window !== 'undefined') {
  if (!window.localStorage || typeof window.localStorage.getItem !== 'function') {
    Object.defineProperty(window, 'localStorage', {
      value: createMemoryStorage(),
      configurable: true,
    })
  }
  if (!window.sessionStorage || typeof window.sessionStorage.getItem !== 'function') {
    Object.defineProperty(window, 'sessionStorage', {
      value: createMemoryStorage(),
      configurable: true,
    })
  }
}

// Limpieza entre tests para no filtrar tokens.
beforeEach(() => {
  if (typeof window !== 'undefined' && window.localStorage?.clear) {
    window.localStorage.clear()
  }
})
