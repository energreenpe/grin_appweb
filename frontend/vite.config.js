import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // pdfjs-dist (usado por react-pdf en el módulo LIST) no debe pre-empaquetarse:
  // su worker se importa como asset (?url).
  optimizeDeps: {
    exclude: ['pdfjs-dist'],
  },
})
