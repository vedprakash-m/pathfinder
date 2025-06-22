import React from 'react'
import ReactDOM from 'react-dom/client'
import { FluentProvider, webLightTheme } from '@fluentui/react-components'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MsalProvider } from '@azure/msal-react'
import { PublicClientApplication } from '@azure/msal-browser'
import { Toaster } from 'react-hot-toast'
import App from './App.tsx'
import msalConfig from './msal-config.ts'
import { AuthProvider } from './contexts/AuthContext'
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

// Initialize MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

// Debug logging for development
if (import.meta.env.DEV) {
  console.log('MSAL Config:', {
    authority: msalConfig.auth.authority,
    clientId: msalConfig.auth.clientId ? `${msalConfig.auth.clientId.substring(0, 8)}...` : 'MISSING',
    redirectUri: msalConfig.auth.redirectUri,
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MsalProvider instance={msalInstance}>
      <AuthProvider>
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
      </AuthProvider>
    </MsalProvider>
  </React.StrictMode>,
)