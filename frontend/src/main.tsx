import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import '@/styles/globals.css'
import { Toaster } from 'sonner'
import { ErrorBoundary } from './components/ErrorBoundary'
import { initTheme } from '@/lib/theme'

// Inicializar tema antes de renderizar
initTheme()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
      <Toaster richColors position="top-right" />
    </ErrorBoundary>
  </React.StrictMode>
)
