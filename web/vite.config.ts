import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const api = process.env.API_PORT ?? '8100'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Ports 5180/8100 avoid clashing with other local projects on Vite's/uvicorn's defaults.
    port: 5180,
    strictPort: true,
    // Local dev: the dashboard talks to FastAPI through the same origin, as in production (where
    // FastAPI serves the built dashboard itself). API_PORT runs a second copy beside the usual one.
    proxy: {
      '/api': `http://localhost:${api}`,
      '/ws': { target: `ws://localhost:${api}`, ws: true },
    },
  },
})
