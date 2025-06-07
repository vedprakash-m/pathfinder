import React from 'react'
import ReactDOM from 'react-dom/client'
import { FluentProvider, webLightTheme } from '@fluentui/react-components'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Auth0Provider } from '@auth0/auth0-react'
import { Toaster } from 'react-hot-toast'
import App from './App.tsx'
import auth0Config from './auth0-config.ts'
import { Auth0ApiProvider } from './components/providers/Auth0ApiProvider'
import './styles/index.css'

// Create a client with optimized caching configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// Auth0 configuration is now imported from auth0-config.ts with hardcoded values

// Debug logging for development
if (import.meta.env.DEV) {
  console.log('Auth0 Config:', {
    domain: auth0Config.domain,
    clientId: auth0Config.clientId ? `${auth0Config.clientId.substring(0, 8)}...` : 'MISSING',
    audience: auth0Config.authorizationParams.audience,
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Auth0Provider {...auth0Config}>
      <Auth0ApiProvider>
        <QueryClientProvider client={queryClient}>
          <FluentProvider theme={webLightTheme}>
            <BrowserRouter>
              <App />
              <Toaster
                position="top-right"
                toastOptions={{
                  duration: 4000,
                  style: {
                    background: '#363636',
                    color: '#fff',
                  },
                  success: {
                    style: {
                      background: '#10b981',
                    },
                  },
                  error: {
                    style: {
                      background: '#ef4444',
                    },
                  },
                }}
              />
            </BrowserRouter>
          </FluentProvider>
        </QueryClientProvider>
      </Auth0ApiProvider>
    </Auth0Provider>
  </React.StrictMode>,
)