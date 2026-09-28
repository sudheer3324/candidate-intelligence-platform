import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev mode (npm run dev) we proxy /api to the FastAPI backend on :8000.
// In production the built files are served BY FastAPI itself, so /api is
// same-origin and no proxy is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
})
