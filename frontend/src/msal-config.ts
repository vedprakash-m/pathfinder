// Microsoft Entra ID (MSAL) configuration for Consumer Authentication
// Uses the /consumers endpoint for personal Microsoft accounts (no user provisioning needed)

import { Configuration, LogLevel } from '@azure/msal-browser';

// Client ID from environment - this MUST be from an app registration configured for consumers
// To create: Azure Portal → App Registrations → New → Supported account types:
//   "Accounts in any organizational directory and personal Microsoft accounts"
const clientId = import.meta.env.VITE_ENTRA_EXTERNAL_CLIENT_ID || 'test-client-id';

// Authority endpoints:
// - /consumers  = Personal Microsoft accounts only (outlook.com, hotmail.com, live.com)
// - /common     = Both personal AND work/school accounts
// - /organizations = Work/school accounts only (any Azure AD tenant)
// - /{tenant-id}   = Specific tenant only

const msalConfig: Configuration = {
  auth: {
    clientId: clientId,
    // Use 'consumers' endpoint for personal Microsoft accounts
    // This requires the app registration to support personal accounts
    // No user provisioning needed - any Microsoft personal account can sign in
    authority: 'https://login.microsoftonline.com/consumers',
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
  scopes: ['openid', 'profile', 'email', 'User.Read'],
  prompt: 'select_account' as const,
};

// Scopes for our backend API calls
// For consumer apps, we use the ID token for authentication to our own backend
// The backend validates the token using Microsoft's public keys
export const apiRequest = {
  scopes: ['openid', 'profile', 'email'],
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
