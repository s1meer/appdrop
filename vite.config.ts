import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  server: {
    port: 1420,
    proxy: {
      '/api': 'http://127.0.0.1:8742',
    }
  }
})
