import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Le site construit (npm run build -> dist/) est servi par le serveur du catalogue lui-même
// (python catalogue.py demarrer), sur http://127.0.0.1:5174 : même adresse pour le site et l'API.
// `npm run dev` (facultatif, pour modifier l'interface) relaie /api vers CE serveur du catalogue.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      port: 5176,
      host: '127.0.0.1',
      strictPort: true,
      proxy: { '/api': { target: env.VITE_PROXY_TARGET || 'http://127.0.0.1:5174', changeOrigin: true } },
    },
  }
})
