import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Read the shared monorepo .env so the final frontend uses the same API
  // and Supabase configuration as the rest of the application.
  envDir: '..',
})
