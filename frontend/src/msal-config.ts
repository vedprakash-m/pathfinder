// Microsoft Entra ID (MSAL) configuration
// Uses vedid.onmicrosoft.com tenant for authentication

import { Configuration, LogLevel } from '@azure/msal-browser';

// Configuration from environment variables
const tenantId = import.meta.env.VITE_ENTRA_EXTERNAL_TENANT_ID || 'vedid.onmicrosoft.com';
const clientId = import.meta.env.VITE_ENTRA_EXTERNAL_CLIENT_ID || 'test-client-id';

const msalConfig: Configuration = {
  auth: {
    clientId: clientId,
    // Use tenant-specific endpoint for vedid.onmicrosoft.com
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: typeof window !== 'undefined'
      ? window.location.origin
      : 'https://icy-wave-01484131e.1.azurestaticapps.net',
    postLogoutRedirectUri: typeof window !== 'undefined'
      ? window.location.origin
      : 'https://icy-wave-01484131e.1.azurestaticapps.net',
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: 'sessionStorage', // ✅ Required for SSO across Vedprakash apps
    storeAuthStateInCookie: true,    // ✅ Required for Safari/iOS SSO support
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
      piiLoggingEnabled: false  // ✅ Required: Disable PII logging for security
    },
    windowHashTimeout: 60000,
    iframeHashTimeout: 6000,
  },
};

// Scopes for login - basic profile info
export const loginRequest = {
  scopes: ['openid', 'profile', 'email'],
  prompt: 'select_account' as const,
};

// Scopes for our backend API
export const apiRequest = {
  scopes: [`api://${clientId}/access_as_user`],
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
  cacheLocation: msalConfig.cache?.cacheLocation,
  storeAuthStateInCookie: msalConfig.cache?.storeAuthStateInCookie,
});

// Validate cache configuration for SSO
if (msalConfig.cache?.cacheLocation !== 'sessionStorage') {
  console.warn('⚠️ MSAL cache configuration may break SSO across apps!');
  console.warn('Current cacheLocation:', msalConfig.cache?.cacheLocation);
  console.warn('Required for SSO: sessionStorage');
}

if (!msalConfig.cache?.storeAuthStateInCookie) {
  console.warn('⚠️ MSAL cookie configuration may break SSO on Safari/iOS!');
  console.warn('Required for Safari SSO: storeAuthStateInCookie: true');
}

export default msalConfig;
export { tenantId, clientId };
