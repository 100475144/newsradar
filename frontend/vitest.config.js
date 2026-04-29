import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Configuración independiente para vitest. Mantenemos vite.config.ts para
// dev/build sin tocarlo.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    include: ['src/**/*.test.{js,jsx,ts,tsx}'],
    css: false,
  },
})
