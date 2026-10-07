import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Ports 5180/8100 avoid clashing with other local projects on Vite's/uvicorn's defaults.
    port: 5180,
    strictPort: true,
    // Local dev: the dashboard talks to FastAPI on :8100 through the same origin,
    // matching production (Cloudflare Worker proxies /api and /ws to the backend).
    proxy: {
      '/api': 'http://localhost:8100',
      '/ws': { target: 'ws://localhost:8100', ws: true },
    },
  },
})
