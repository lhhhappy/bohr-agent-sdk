import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'ui-static',
  },
  server: {
    // Use environment variable or default to 3000 for dev server
    port: parseInt(process.env.FRONTEND_PORT || '3000'),
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: {
      // Proxy API and WebSocket requests to the backend server
      '/api/materials_db': {
        target: `https://www.test.bohrium.com`,
        changeOrigin: true,
      },
      '/api': {
        target: `http://localhost:${process.env.VITE_WS_PORT || '8000'}`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://localhost:${process.env.VITE_WS_PORT || '8000'}`,
        ws: true,
        changeOrigin: true,
      },
    }
  }
})