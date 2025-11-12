import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor libraries
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],

          // Split heavy pages into separate chunks
          'pages-analytics': [
            './src/pages/Analytics.tsx',
            './src/pages/AnalyticsSample.tsx',
          ],
          'pages-strategies': [
            './src/pages/StrategyResults.tsx',
            './src/pages/PreGameStrategyResults.tsx',
            './src/pages/StrategySettings.tsx',
          ],
          'pages-tools': [
            './src/pages/Alerts.tsx',
            './src/pages/Odds.tsx',
            './src/pages/MaxEvEdges.tsx',
            './src/pages/Tools.tsx',
          ],
          'pages-admin': [
            './src/pages/AdminDashboard.tsx',
            './src/pages/Settings.tsx',
          ],
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  }
})
