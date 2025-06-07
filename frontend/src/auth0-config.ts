// Auth0 configuration using environment variables for security
// Fallback to hardcoded values only for development

const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN || 'dev-jwnud3v8ghqnyygr.us.auth0.com',
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || 'KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn',
  authorizationParams: {
    redirect_uri: typeof window !== 'undefined' 
      ? window.location.origin 
      : 'https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io',
    audience: import.meta.env.VITE_AUTH0_AUDIENCE || 'https://pathfinder-api.com',
  },
  useRefreshTokens: true,
  cacheLocation: 'localstorage' as const,
}

// Debug logging to verify configuration is loaded correctly
console.log('🔧 Auth0 Config Loaded:', {
  domain: auth0Config.domain,
  clientId: auth0Config.clientId ? `${auth0Config.clientId.substring(0, 8)}...` : 'MISSING',
  audience: auth0Config.authorizationParams.audience,
  redirect_uri: auth0Config.authorizationParams.redirect_uri,
});

// Validate configuration
if (!auth0Config.domain || !auth0Config.clientId) {
  console.error('❌ Auth0 configuration is missing required fields!');
  console.error('Domain:', auth0Config.domain);
  console.error('Client ID:', auth0Config.clientId ? 'Present' : 'MISSING');
}

export default auth0Config;
