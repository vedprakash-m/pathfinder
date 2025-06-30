# Vedprakash Domain Authentication Requirements
## Microsoft Entra ID Integration Standards

**Document Purpose**: High-level authentication requirements for any Vedprakash domain application.

**Target Audience**: Development teams implementing authentication in Vedprakash apps.

**Last Updated**: June 28, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Requirements](#authentication-requirements)
3. [Frontend Integration](#frontend-integration)
4. [Backend Integration](#backend-integration)
5. [User Object Standard](#user-object-standard)
6. [API Requirements](#api-requirements)
7. [Configuration](#configuration)
8. [Validation](#validation)
9. [Critical Security Considerations](#critical-security-considerations)

---

## Overview

### Why Unified Authentication?

The Vedprakash domain currently operates **five independent applications** with **five different authentication systems**:

| Application | Current Auth System | Issues |
|-------------|-------------------|---------|
| **Sutra (sutra.vedprakash.net)** | Firebase Authentication | Isolated user base, no cross-app integration |
| **Vimarsh (vimarsh.vedprakash.net)** | Supabase Authentication | Separate user accounts, manual user management |
| **Vigor (vigor.vedprakash.net)** | Custom JWT System | Security maintenance overhead, no SSO |
| **Pathfinder (pathfinder.vedprakash.net)** | Auth0 + Entra ID | Mixed systems, complexity and cost |
| **VCarpool (carpool.vedprakash.net)** | Custom JWT System | Duplicated effort, security concerns |

### Business Problems We're Solving

#### 1. **Poor User Experience**
- Users must create **separate accounts** for each app
- **No single sign-on** - users log in repeatedly
- **Password fatigue** - users struggle with multiple credentials
- **Account confusion** - users forget which email they used for which app

#### 2. **Operational Complexity**
- **Five different auth systems** to maintain and secure
- **Fragmented user data** across multiple platforms
- **Inconsistent security policies** across applications
- **Higher support burden** - users contact support for password resets across multiple systems

#### 3. **Development Inefficiency**
- **Duplicated authentication code** across teams
- **Different integration patterns** for each auth system
- **Inconsistent user objects** and permissions models
- **Increased development time** for cross-app features

#### 4. **Security and Compliance Risks**
- **Multiple attack surfaces** across different auth providers
- **Inconsistent security policies** and practices
- **Audit complexity** with multiple authentication logs
- **Harder compliance** with data protection regulations

#### 5. **Cost and Scalability**
- **Multiple vendor costs** (Auth0, Firebase, Supabase, custom infrastructure)
- **Licensing complexity** as user base grows
- **Operational overhead** managing multiple systems
- **Limited economies of scale**

### Business Benefits of Unified Authentication

#### 🚀 **Enhanced User Experience**
- **Single Sign-On**: Login once, access all Vedprakash apps
- **Unified Profile**: One account, one profile across all services
- **Seamless Navigation**: Move between apps without re-authentication
- **Professional Experience**: Enterprise-grade authentication flow

#### 💰 **Cost Optimization**
- **Eliminate Auth0 costs**: Save ~$240-480/month in licensing
- **Reduce Firebase/Supabase dependency**: Lower operational costs
- **Free Entra ID tier**: Up to 50,000 users at no cost
- **Consolidated billing**: Single Microsoft Azure invoice

#### 🔒 **Improved Security Posture**
- **Enterprise-grade security**: Microsoft's battle-tested authentication
- **Centralized security policies**: Consistent MFA, conditional access
- **Single audit trail**: All authentication events in one place
- **Reduced attack surface**: One authentication system to secure

#### ⚡ **Development Efficiency**
- **Consistent authentication patterns** across all apps
- **Shared user objects** and permissions model
- **Faster feature development** with unified user context
- **Reduced maintenance overhead** for authentication code

#### 📈 **Business Growth Enablement**
- **Cross-app analytics**: Unified user journey tracking
- **Integrated billing**: Single subscription across all apps
- **Collaborative features**: Users can share data between apps
- **Enterprise readiness**: B2B customers expect SSO

### Technical Benefits

#### 🏗️ **Architectural Consistency**
- **Standardized JWT tokens** across all applications
- **Consistent user object interface** for all teams
- **Unified API authentication** patterns
- **Predictable security model** across the domain

#### 🔄 **Future-Proof Design**
- **Scalable to enterprise customers** who require SSO
- **Support for advanced features** (MFA, conditional access, B2B collaboration)
- **Integration ready** for Microsoft ecosystem (Office 365, Teams, etc.)
- **Compliance ready** for enterprise security requirements

### Migration Impact Assessment

#### ✅ **Low Risk Applications**
- **Pathfinder**: Already partially using Entra ID
- **Minimal code changes** required

#### ⚠️ **Medium Risk Applications**
- **Vigor & VCarpool**: Custom JWT systems need replacement
- **Database user ID migration** required
- **Testing required** for existing user workflows

#### 🔧 **Higher Effort Applications**
- **Sutra & Vimarsh**: Third-party auth provider replacement
- **User migration scripts** needed
- **Database schema updates** required
- **Comprehensive testing** of all user flows

### Success Metrics

We'll measure success through:

#### User Experience
- **Reduced login friction**: Measure login completion rates
- **Cross-app usage**: Track users accessing multiple apps
- **Support ticket reduction**: Fewer password/account issues

#### Technical Performance  
- **Authentication response times**: <2 seconds for login
- **SSO success rate**: >95% successful cross-app authentication
- **System reliability**: 99.9% authentication uptime

#### Business Impact
- **Cost reduction**: Eliminate external auth provider costs
- **Development velocity**: Faster feature shipping with unified auth
- **Enterprise readiness**: Support B2B customers requiring SSO

---

### Authentication Standard

All Vedprakash domain applications **MUST** use Microsoft Entra ID as the sole authentication provider. Each app can implement this using their preferred authentication libraries and patterns.

### Key Benefits
- **Single Sign-On**: Seamless authentication across all `.vedprakash.net` apps
- **Enterprise Security**: Microsoft Entra ID's enterprise-grade security
- **Implementation Flexibility**: Use your preferred authentication libraries
- **Centralized Management**: Unified user management and permissions

### What This Means for Your App
- Implement Microsoft Entra ID authentication using any compatible library
- Update your backend to validate Microsoft Entra ID JWT tokens
- Use the standardized user object interface
- Implement proper API authentication headers

---

## Authentication Requirements

### Core Standards

| Requirement | Specification |
|------------|---------------|
| **Identity Provider** | Microsoft Entra ID (`vedid.onmicrosoft.com`) |
| **Authentication Method** | OAuth 2.0 / OpenID Connect |
| **Token Format** | JWT tokens from Microsoft Entra ID |
| **Session Management** | Stateless authentication via JWT |
| **Single Sign-On** | Cross-domain SSO across `.vedprakash.net` |

### Recommended Libraries

Choose the authentication library that works best for your stack:

| Framework | Recommended Library | Alternative |
|-----------|-------------------|-------------|
| **React/Next.js** | `@azure/msal-react` | `next-auth` with Azure AD provider |
| **Vue/Nuxt.js** | `@azure/msal-browser` | `@nuxtjs/auth-next` with Azure AD |
| **Svelte/SvelteKit** | `@azure/msal-browser` | Custom implementation |
| **Node.js Backend** | `@azure/msal-node` | `passport-azure-ad` |
| **Python** | `msal` | `django-auth-adfs` |
| **C#/.NET** | `Microsoft.AspNetCore.Authentication.AzureAD` | Built-in |

### Installation Examples

```bash
# React/Next.js
npm install @azure/msal-react @azure/msal-browser

# Vue/Nuxt.js  
npm install @azure/msal-browser

# Node.js backend
npm install @azure/msal-node

# Python
pip install msal
```

### Authentication Flow

1. User visits your app
2. App checks authentication status via your chosen authentication library
3. If not authenticated, redirect to Microsoft Entra ID login
4. After successful login, receive standardized user object
5. Include JWT token in all API requests

---

## Frontend Integration

### 1. Authentication Setup

**Requirement**: Implement Microsoft Entra ID authentication using your preferred library.

#### React/Next.js Example (using @azure/msal-react)

```tsx
// _app.tsx
import { MsalProvider } from '@azure/msal-react';
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: 'your-app-client-id',
    authority: 'https://login.microsoftonline.com/vedid.onmicrosoft.com',
    redirectUri: 'https://yourapp.vedprakash.net',
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
};

const msalInstance = new PublicClientApplication(msalConfig);

export default function App({ Component, pageProps }) {
  return (
    <MsalProvider instance={msalInstance}>
      <Component {...pageProps} />
    </MsalProvider>
  );
}
```

#### Vue/Nuxt.js Example (using @azure/msal-browser)

```typescript
// plugins/auth.client.ts
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: 'your-app-client-id',
    authority: 'https://login.microsoftonline.com/vedid.onmicrosoft.com',
    redirectUri: 'https://yourapp.vedprakash.net',
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export default defineNuxtPlugin(async () => {
  await msalInstance.initialize();
  return {
    provide: {
      msal: msalInstance
    }
  };
});
```

### 2. Authentication Logic

**Requirement**: Implement login, logout, and authentication state management.

#### React Example

```tsx
import { useMsal } from '@azure/msal-react';
import { loginRequest } from '../config/authConfig';

function AuthComponent() {
  const { instance, accounts, inProgress } = useMsal();
  const isAuthenticated = accounts.length > 0;

  const handleLogin = () => {
    instance.loginRedirect(loginRequest);
  };

  const handleLogout = () => {
    instance.logoutRedirect();
  };

  if (inProgress === 'login') {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <button onClick={handleLogin}>Sign In</button>;
  }

  const user = accounts[0];
  return (
    <div>
      <h1>Welcome, {user.name}!</h1>
      <button onClick={handleLogout}>Sign Out</button>
    </div>
  );
}
```

#### Vue Example

```vue
<template>
  <div>
    <div v-if="isLoading">Loading...</div>
    <button v-else-if="!isAuthenticated" @click="login">Sign In</button>
    <div v-else>
      <h1>Welcome, {{ user.name }}!</h1>
      <button @click="logout">Sign Out</button>
    </div>
  </div>
</template>

<script setup>
const { $msal } = useNuxtApp();
const isLoading = ref(true);
const isAuthenticated = ref(false);
const user = ref(null);

onMounted(async () => {
  const accounts = $msal.getAllAccounts();
  if (accounts.length > 0) {
    isAuthenticated.value = true;
    user.value = accounts[0];
  }
  isLoading.value = false;
});

const login = () => {
  $msal.loginRedirect({
    scopes: ['openid', 'profile', 'email'],
  });
};

const logout = () => {
  $msal.logoutRedirect();
};
</script>
```

### 3. Protected Routes

**Requirement**: Protect routes based on authentication state.

```tsx
// React example
import { useIsAuthenticated } from '@azure/msal-react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

function ProtectedPage() {
  const isAuthenticated = useIsAuthenticated();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  return <div>Your protected content</div>;
}
```

### 4. API Calls with Tokens

**Requirement**: Include authentication token in all API requests.

#### React Example (using @azure/msal-react)

```tsx
import { useMsal } from '@azure/msal-react';

function useApiCall() {
  const { instance, accounts } = useMsal();

  const getAccessToken = async () => {
    if (accounts.length === 0) return null;

    const request = {
      scopes: ['your-api-scope'],
      account: accounts[0],
    };

    try {
      const response = await instance.acquireTokenSilent(request);
      return response.accessToken;
    } catch (error) {
      // Fallback to interactive token acquisition
      const response = await instance.acquireTokenRedirect(request);
      return response.accessToken;
    }
  };

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getAccessToken();
    
    return fetch(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
  };

  return { apiCall };
}

// Usage
function DataComponent() {
  const { apiCall } = useApiCall();
  
  const fetchData = async () => {
    const response = await apiCall('/api/user-data');
    const data = await response.json();
    // Handle data
  };
  
  return <button onClick={fetchData}>Load Data</button>;
}
```

#### Vue Example

```typescript
// composables/useApi.ts
export const useApi = () => {
  const { $msal } = useNuxtApp();

  const getAccessToken = async () => {
    const accounts = $msal.getAllAccounts();
    if (accounts.length === 0) return null;

    const request = {
      scopes: ['your-api-scope'],
      account: accounts[0],
    };

    try {
      const response = await $msal.acquireTokenSilent(request);
      return response.accessToken;
    } catch (error) {
      const response = await $msal.acquireTokenRedirect(request);
      return response.accessToken;
    }
  };

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getAccessToken();
    
    return $fetch(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
      },
    });
  };

  return { apiCall };
};
```

### 1. Token Validation

**Requirement**: Validate Microsoft Entra ID JWT tokens on all protected endpoints.

```javascript
// Express.js example
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

const client = jwksClient({
  jwksUri: 'https://login.microsoftonline.com/vedid.onmicrosoft.com/discovery/v2.0/keys'
});

function getKey(header, callback) {
  client.getSigningKey(header.kid, (err, key) => {
    const signingKey = key.publicKey || key.rsaPublicKey;
    callback(null, signingKey);
  });
}

function validateToken(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Access token required' });
  }

  const token = authHeader.substring(7);
  
  jwt.verify(token, getKey, {
    audience: 'your-app-client-id',
    issuer: 'https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0',
    algorithms: ['RS256']
  }, (err, decoded) => {
    if (err) {
      return res.status(401).json({ error: 'Invalid token' });
    }
    
    req.user = decoded;
    next();
  });
}

// Apply to protected routes
app.get('/api/protected', validateToken, (req, res) => {
  res.json({ message: 'Access granted', user: req.user });
});
```

### 2. User Object from Token

**Requirement**: Extract user information from validated JWT token claims.

```javascript
function extractUser(tokenClaims) {
  return {
    id: tokenClaims.sub,
    email: tokenClaims.email,
    name: tokenClaims.name,
    givenName: tokenClaims.given_name,
    familyName: tokenClaims.family_name,
    permissions: tokenClaims.roles || [],
    vedProfile: {
      profileId: tokenClaims.ved_profile_id,
      subscriptionTier: tokenClaims.ved_subscription_tier,
      appsEnrolled: tokenClaims.ved_apps_enrolled || [],
      preferences: JSON.parse(tokenClaims.ved_preferences || '{}')
    }
  };
}
```

### 3. Framework-Specific Examples

#### Python/FastAPI Example

```python
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests

security = HTTPBearer()

def get_jwks():
    jwks_uri = "https://login.microsoftonline.com/vedid.onmicrosoft.com/discovery/v2.0/keys"
    return requests.get(jwks_uri).json()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        jwks = get_jwks()
        token = credentials.credentials
        
        decoded = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="your-app-client-id",
            issuer="https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0"
        )
        
        return decoded
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

@app.get("/api/protected")
async def protected_endpoint(current_user: dict = Depends(verify_token)):
    return {"user": current_user}
```

#### C#/.NET Example

```csharp
// Startup.cs or Program.cs
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = "https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0";
        options.Audience = "your-app-client-id";
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true
        };
    });

// Controller
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ProtectedController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        var user = HttpContext.User;
        return Ok(new { User = user.Identity.Name });
    }
}
```

---

## User Object Standard

### Interface Definition

**Requirement**: Use this exact user object interface across your application.

```typescript
interface VedUser {
  id: string;           // Entra ID subject claim (primary user identifier)
  email: string;        // User's email address
  name: string;         // Full display name
  givenName: string;    // First name
  familyName: string;   // Last name
  permissions: string[]; // App-specific permissions from JWT claims
  vedProfile: {
    profileId: string;                           // Vedprakash domain profile ID
    subscriptionTier: 'free' | 'premium' | 'enterprise';
    appsEnrolled: string[];                      // List of enrolled apps
    preferences: Record<string, any>;            // User preferences
  };
}
```

### Usage Guidelines

- **Primary Key**: Always use `user.id` as the primary user identifier
- **Display**: Use `user.name` for user display names
- **Email**: Use `user.email` for communication
- **Permissions**: Check `user.permissions` for app-specific access control
- **Profile**: Access Vedprakash-specific data via `user.vedProfile`

---

## API Requirements

### 1. Frontend API Calls

**Requirement**: Include authentication token in all API requests.

#### React Example (using @azure/msal-react)

```tsx
import { useMsal } from '@azure/msal-react';

function useApiCall() {
  const { instance, accounts } = useMsal();

  const getAccessToken = async () => {
    if (accounts.length === 0) return null;

    const request = {
      scopes: ['your-api-scope'],
      account: accounts[0],
    };

    try {
      const response = await instance.acquireTokenSilent(request);
      return response.accessToken;
    } catch (error) {
      // Fallback to interactive token acquisition
      const response = await instance.acquireTokenRedirect(request);
      return response.accessToken;
    }
  };

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getAccessToken();
    
    return fetch(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
  };

  return { apiCall };
}

// Usage
function DataComponent() {
  const { apiCall } = useApiCall();
  
  const fetchData = async () => {
    const response = await apiCall('/api/user-data');
    const data = await response.json();
    // Handle data
  };
  
  return <button onClick={fetchData}>Load Data</button>;
}
```

#### Vue Example

```typescript
// composables/useApi.ts
export const useApi = () => {
  const { $msal } = useNuxtApp();

  const getAccessToken = async () => {
    const accounts = $msal.getAllAccounts();
    if (accounts.length === 0) return null;

    const request = {
      scopes: ['your-api-scope'],
      account: accounts[0],
    };

    try {
      const response = await $msal.acquireTokenSilent(request);
      return response.accessToken;
    } catch (error) {
      const response = await $msal.acquireTokenRedirect(request);
      return response.accessToken;
    }
  };

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getAccessToken();
    
    return $fetch(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
      },
    });
  };

  return { apiCall };
};
```

### 2. Backend API Response Format

**Requirement**: Return consistent error responses for authentication failures.

```javascript
// Unauthorized (no token)
res.status(401).json({
  error: 'Access token required',
  code: 'AUTH_TOKEN_MISSING'
});

// Invalid token
res.status(401).json({
  error: 'Invalid or expired token',
  code: 'AUTH_TOKEN_INVALID'
});

// Insufficient permissions
res.status(403).json({
  error: 'Insufficient permissions',
  code: 'AUTH_PERMISSION_DENIED'
});
```

---

## Configuration

### Microsoft Entra ID App Registration

**Requirement**: Each app must be registered in Microsoft Entra ID with proper configuration.

#### App Registration Settings

```json
{
  "name": "YourApp - Vedprakash Domain",
  "clientId": "your-app-client-id",
  "redirectUris": [
    "https://yourapp.vedprakash.net",
    "https://yourapp.vedprakash.net/auth/callback"
  ],
  "scopes": [
    "openid",
    "profile", 
    "email",
    "your-app-specific-scopes"
  ],
  "tokenConfiguration": {
    "accessTokenAcceptedVersion": 2,
    "optionalClaims": {
      "accessToken": [
        {"name": "given_name"},
        {"name": "family_name"},
        {"name": "email"}
      ]
    }
  }
}
```

### Environment Variables

**Requirement**: Configure these environment variables for your app.

```bash
# Frontend Configuration
NEXT_PUBLIC_AZURE_AD_CLIENT_ID=your-app-client-id
NEXT_PUBLIC_AZURE_AD_TENANT_ID=vedid.onmicrosoft.com
NEXT_PUBLIC_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/vedid.onmicrosoft.com

# Backend Configuration  
AZURE_AD_CLIENT_ID=your-app-client-id
AZURE_AD_TENANT_ID=vedid.onmicrosoft.com
AZURE_AD_CLIENT_SECRET=your-app-client-secret

# API Scopes
AZURE_AD_SCOPES=openid,profile,email,your-app-scope
```

### Framework-Specific Configuration Files

#### React/Next.js Configuration

```typescript
// config/authConfig.ts
export const msalConfig = {
  auth: {
    clientId: process.env.NEXT_PUBLIC_AZURE_AD_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_AZURE_AD_TENANT_ID}`,
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: ['openid', 'profile', 'email'],
};

export const apiRequest = {
  scopes: ['your-api-scope'],
};
```

#### Vue/Nuxt Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      azureAd: {
        clientId: process.env.AZURE_AD_CLIENT_ID,
        tenantId: process.env.AZURE_AD_TENANT_ID,
        authority: `https://login.microsoftonline.com/${process.env.AZURE_AD_TENANT_ID}`,
      }
    }
  }
});
```

### Security Headers

**Requirement**: Add these security headers to all responses.

```javascript
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  next();
});
```

---

## Validation

### Implementation Checklist

**Frontend Requirements**:
- [ ] Microsoft Entra ID authentication library installed and configured
- [ ] App wrapped with authentication provider
- [ ] Login/logout functionality implemented
- [ ] Protected routes redirect unauthenticated users
- [ ] API calls include `Authorization: Bearer <token>` header
- [ ] Token refresh handled automatically

**Backend Requirements**:
- [ ] JWT token validation implemented for Microsoft Entra ID
- [ ] Protected endpoints verify tokens before processing
- [ ] User object extracted from token claims using standard interface
- [ ] Proper HTTP error responses for authentication failures
- [ ] Security headers configured correctly

**Configuration Requirements**:
- [ ] App registered in Microsoft Entra ID
- [ ] Environment variables configured
- [ ] Redirect URIs properly set
- [ ] API scopes defined and configured
- [ ] Optional claims configured for user data

**Testing Requirements**:
- [ ] Login/logout flow works correctly
- [ ] Protected routes deny access to unauthenticated users
- [ ] API calls with valid tokens succeed
- [ ] API calls without tokens return 401 Unauthorized
- [ ] User object contains all required properties
- [ ] Cross-app SSO works (user stays logged in across Vedprakash apps)

### Success Criteria

Your authentication implementation is complete when:

1. **Users can sign in** with their Microsoft account through Entra ID
2. **Single sign-on works** - users stay logged in across all Vedprakash apps
3. **Protected content** is only accessible to authenticated users
4. **API requests** properly include and validate authentication tokens
5. **User information** follows the standardized interface and is available throughout your app
6. **Token management** handles refresh automatically without user intervention

---

## Critical Security Considerations

### ⚠️ **IMPORTANT**: These requirements are mandatory for all implementations

#### 1. JWKS Caching (Required)
**Risk**: Fetching JWKS on every request causes performance issues and potential rate limiting.

```javascript
// ✅ REQUIRED: Implement JWKS caching
const NodeCache = require('node-cache');
const jwksCache = new NodeCache({ stdTTL: 3600 }); // 1 hour cache

function getKey(header, callback) {
  const cacheKey = `jwks_${header.kid}`;
  let key = jwksCache.get(cacheKey);
  
  if (key) {
    return callback(null, key);
  }
  
  client.getSigningKey(header.kid, (err, key) => {
    if (err) return callback(err);
    
    const signingKey = key.publicKey || key.rsaPublicKey;
    jwksCache.set(cacheKey, signingKey);
    callback(null, signingKey);
  });
}
```

#### 2. Standardized User Extraction (Required)
**Risk**: Inconsistent user object creation across apps.

```javascript
// ✅ REQUIRED: Use this exact function for user extraction
function extractStandardUser(tokenClaims) {
  // Validate required claims
  if (!tokenClaims.sub || !tokenClaims.email) {
    throw new Error('Invalid token: missing required claims');
  }
  
  return {
    id: tokenClaims.sub,
    email: tokenClaims.email,
    name: tokenClaims.name || tokenClaims.preferred_username,
    givenName: tokenClaims.given_name || '',
    familyName: tokenClaims.family_name || '',
    permissions: tokenClaims.roles || [],
    vedProfile: {
      profileId: tokenClaims.ved_profile_id || tokenClaims.sub,
      subscriptionTier: tokenClaims.ved_subscription_tier || 'free',
      appsEnrolled: Array.isArray(tokenClaims.ved_apps_enrolled) 
        ? tokenClaims.ved_apps_enrolled 
        : [],
      preferences: (() => {
        try {
          return typeof tokenClaims.ved_preferences === 'string' 
            ? JSON.parse(tokenClaims.ved_preferences) 
            : tokenClaims.ved_preferences || {};
        } catch {
          return {};
        }
      })()
    }
  };
}
```

#### 3. Enhanced Error Handling (Required)
**Risk**: Silent authentication failures lead to poor user experience.

```typescript
// ✅ REQUIRED: Proper error handling in token acquisition
const getAccessToken = async () => {
  if (accounts.length === 0) {
    throw new Error('No authenticated accounts found');
  }

  const request = {
    scopes: ['your-api-scope'],
    account: accounts[0],
  };

  try {
    const response = await instance.acquireTokenSilent(request);
    return response.accessToken;
  } catch (error) {
    console.warn('Silent token acquisition failed, falling back to interactive:', error);
    
    try {
      const response = await instance.acquireTokenRedirect(request);
      return response.accessToken;
    } catch (redirectError) {
      console.error('Token acquisition failed completely:', redirectError);
      throw new Error('Unable to acquire access token');
    }
  }
};
```

#### 4. Complete Security Headers (Required)
**Risk**: Missing security headers expose apps to attacks.

```javascript
// ✅ REQUIRED: Complete security headers
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline' https://login.microsoftonline.com; connect-src 'self' https://login.microsoftonline.com https://*.vedprakash.net");
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  next();
});
```

#### 5. SSO Domain Configuration (Required)
**Risk**: Improper domain configuration breaks cross-app SSO.

```javascript
// ✅ REQUIRED: SSO-compatible MSAL configuration
const msalConfig = {
  auth: {
    clientId: 'your-app-client-id',
    authority: 'https://login.microsoftonline.com/vedid.onmicrosoft.com',
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage', // ✅ Required for SSO
    storeAuthStateInCookie: true,    // ✅ Required for Safari/iOS
  },
  system: {
    allowNativeBroker: false, // ✅ Ensures consistent web experience
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (!containsPii) {
          console.log(message);
        }
      },
      piiLoggingEnabled: false
    }
  }
};
```

#### 6. Production Monitoring (Required)
**Risk**: No visibility into authentication failures in production.

```javascript
// ✅ REQUIRED: Authentication monitoring
function validateToken(req, res, next) {
  const startTime = Date.now();
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    // Log authentication attempt
    console.warn('Authentication failed: No token provided', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      path: req.path
    });
    
    return res.status(401).json({
      error: 'Access token required',
      code: 'AUTH_TOKEN_MISSING'
    });
  }

  const token = authHeader.substring(7);
  
  jwt.verify(token, getKey, {
    audience: 'your-app-client-id',
    issuer: 'https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0',
    algorithms: ['RS256']
  }, (err, decoded) => {
    const duration = Date.now() - startTime;
    
    if (err) {
      // Log authentication failure
      console.error('Authentication failed: Invalid token', {
        error: err.message,
        duration,
        ip: req.ip,
        path: req.path
      });
      
      return res.status(401).json({
        error: 'Invalid or expired token',
        code: 'AUTH_TOKEN_INVALID'
      });
    }
    
    // Log successful authentication
    console.info('Authentication successful', {
      userId: decoded.sub,
      duration,
      path: req.path
    });
    
    req.user = extractStandardUser(decoded);
    next();
  });
}
```

#### 7. Fallback and Resilience (Required)
**Risk**: Authentication service outages break all apps.

```typescript
// ✅ REQUIRED: Graceful degradation strategy
const handleAuthError = (error: any) => {
  // Log error for monitoring
  console.error('Authentication error:', error);
  
  // Provide user-friendly message
  if (error.message?.includes('network')) {
    return 'Connection issue. Please check your internet and try again.';
  }
  
  if (error.message?.includes('timeout')) {
    return 'Authentication is taking longer than usual. Please try again.';
  }
  
  return 'Sign-in temporarily unavailable. Please try again in a few minutes.';
};

// Implement circuit breaker for auth endpoints
let authFailureCount = 0;
const AUTH_FAILURE_THRESHOLD = 5;
const CIRCUIT_RESET_TIME = 300000; // 5 minutes

const checkAuthCircuit = () => {
  if (authFailureCount >= AUTH_FAILURE_THRESHOLD) {
    setTimeout(() => {
      authFailureCount = 0;
    }, CIRCUIT_RESET_TIME);
    
    throw new Error('Authentication service temporarily unavailable');
  }
};
```

---

## Compliance and Governance

### Security Review Requirements

**Before Production Deployment**, each app MUST:

1. **Security Audit**: Complete security review of authentication implementation
2. **Penetration Testing**: Test for common authentication vulnerabilities
3. **Performance Testing**: Verify authentication doesn't impact app performance
4. **SSO Testing**: Verify cross-app SSO functionality works correctly
5. **Error Handling Testing**: Test all error scenarios and fallback mechanisms

### Mandatory Security Checklist

- [ ] JWKS caching implemented with appropriate TTL
- [ ] Standardized user extraction function used
- [ ] Complete security headers configured
- [ ] Error handling covers all failure scenarios
- [ ] Authentication monitoring and logging implemented
- [ ] Token validation uses exact parameters specified
- [ ] SSO configuration tested across multiple apps
- [ ] Fallback mechanisms implemented for service outages
- [ ] Security review completed by security team
- [ ] Performance impact assessment completed

### Support and Escalation

**For Implementation Issues**:
1. Check this requirements document
2. Review Microsoft Entra ID documentation
3. Contact security team for security-related questions
4. Escalate to architecture team for design decisions

**For Production Issues**:
1. Monitor authentication logs for errors
2. Check Azure AD service health
3. Implement graceful degradation
4. Follow incident response procedures
