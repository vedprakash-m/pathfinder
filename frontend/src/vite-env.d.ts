/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AZURE_TENANT_ID: string
  readonly VITE_AZURE_CLIENT_ID: string
  readonly VITE_VAPID_PUBLIC_KEY: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}