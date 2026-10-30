import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Relative asset paths so the build works under any sub-path
  // (e.g. username.github.io/repo/) as well as at a domain root.
  base: './',
})
