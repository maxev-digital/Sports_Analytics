import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './', // Use relative paths for Electron compatibility
  server: {
    port: 5173,
    // Proxy disabled - using production API directly
    // This allows the app to connect to https://max-ev-sports.com/api
    // instead of trying to use a local backend
  }
})
