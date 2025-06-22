// Microsoft Entra External ID (MSAL) configuration
// Replaces Auth0 configuration with Microsoft's identity platform

import { Configuration, LogLevel } from '@azure/msal-browser';

// Get configuration from environment variables
const tenantId = import.meta.env.VITE_ENTRA_EXTERNAL_TENANT_ID || 'test-tenant-id';
const clientId = import.meta.env.VITE_ENTRA_EXTERNAL_CLIENT_ID || 'test-client-id';

const msalConfig: Configuration = {
  auth: {
    clientId: clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: typeof window !== 'undefined' 
      ? window.location.origin 
      : 'https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io',
    postLogoutRedirectUri: typeof window !== 'undefined' 
      ? window.location.origin 
      : 'https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io',
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false, // Set to true for IE11 or Edge legacy
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case LogLevel.Error:
            console.error(message);
            return;
          case LogLevel.Info:
            console.info(message);
            return;
          case LogLevel.Verbose:
            console.debug(message);
            return;
          case LogLevel.Warning:
            console.warn(message);
            return;
          default:
            return;
        }
      },
      logLevel: import.meta.env.NODE_ENV === 'development' ? LogLevel.Verbose : LogLevel.Error,
    },
    allowNativeBroker: false, // Disables WAM Broker
    windowHashTimeout: 60000,
    iframeHashTimeout: 6000,
  },
};

// Scopes for API access
export const loginRequest = {
  scopes: ['openid', 'profile', 'email', 'User.Read'],
  prompt: 'select_account' as const,
};

// Scopes for Graph API (user info)
export const graphRequest = {
  scopes: ['User.Read'],
};

// Debug logging to verify configuration is loaded correctly
console.log('🔧 MSAL Config Loaded:', {
  authority: msalConfig.auth.authority,
  clientId: msalConfig.auth.clientId ? `${msalConfig.auth.clientId.substring(0, 8)}...` : 'MISSING',
  redirectUri: msalConfig.auth.redirectUri,
  tenantId: tenantId,
});

// Validate configuration
if (!tenantId || !clientId || tenantId === 'test-tenant-id' || clientId === 'test-client-id') {
  console.warn('⚠️ MSAL configuration is using test values or missing required fields!');
  console.warn('Tenant ID:', tenantId);
  console.warn('Client ID:', clientId ? 'Present' : 'MISSING');
  
  if (import.meta.env.NODE_ENV === 'production') {
    console.error('❌ Production deployment requires valid Entra External ID configuration!');
  }
}

export default msalConfig;
export { tenantId, clientId }; 