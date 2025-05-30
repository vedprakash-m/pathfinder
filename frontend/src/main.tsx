import React from 'react'
import ReactDOM from 'react-dom/client'
import { FluentProvider, webLightTheme } from '@fluentui/react-components'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Auth0Provider } from '@auth0/auth0-react'
import { Toaster } from 'react-hot-toast'
import App from './App.tsx'
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

// Auth0 configuration
const auth0Config = {
  domain: 'dev-pathfinder.us.auth0.com',
  clientId: 'pathfinder-client-id',
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: 'https://api.pathfinder.com',
  },
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Auth0Provider {...auth0Config}>
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
    </Auth0Provider>
  </React.StrictMode>,
)