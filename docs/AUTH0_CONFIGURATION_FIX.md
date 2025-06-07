# Auth0 Configuration Fix Guide

## Problem
Login button gives errors because Auth0 application settings need proper callback URLs for the production domain.

## Root Cause
The Auth0 application in the dashboard is not configured with the correct callback URLs for:
- **Production Domain**: `https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io`
- **Local Development**: `http://localhost:5173`

## Solution Steps

### 1. Access Auth0 Dashboard
1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Log in with your Auth0 account
3. Navigate to **Applications** → **Applications**
4. Find your application with Client ID: `KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn`

### 2. Configure Application URLs
In the application settings, add these URLs to the appropriate fields:

**Allowed Callback URLs:**
```
https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io,
http://localhost:5173
```

**Allowed Logout URLs:**
```
https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io,
http://localhost:5173
```

**Allowed Web Origins:**
```
https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io,
http://localhost:5173
```

**Allowed Origins (CORS):**
```
https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io,
http://localhost:5173
```

### 3. Advanced Settings
In **Advanced Settings** → **OAuth**:
- **Grant Types**: Ensure `Authorization Code`, `Refresh Token`, and `Implicit` are enabled
- **JSON Web Token (JWT) Signature Algorithm**: `RS256`

### 4. Save Configuration
Click **Save Changes** at the bottom of the page.

### 5. Test Login
1. Go to: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io
2. Click the "Sign In / Sign Up" button
3. You should be redirected to Auth0 login page
4. After successful login, you should be redirected back to `/dashboard`

## Verification
The Auth0Debug component on the login page shows:
- Domain: `dev-jwnud3v8ghqnyygr.us.auth0.com`
- Client ID: `KXu3KpG...`
- Redirect URI: Should match current domain
- Any error messages will be displayed

## Common Issues

### Issue: "redirect_uri_mismatch"
**Cause**: Callback URL not properly configured in Auth0 dashboard
**Solution**: Ensure exact URL match in Allowed Callback URLs

### Issue: "Access denied"
**Cause**: User doesn't exist or application not properly configured
**Solution**: Check if user signup is enabled in Auth0 dashboard

### Issue: "Invalid audience"
**Cause**: API audience mismatch
**Solution**: Verify audience matches in both frontend config and Auth0 API settings

## Next Steps After Fix
Once login is working:
1. Test user registration flow
2. Test logout functionality
3. Verify token refresh works
4. Test role-based access to protected routes
5. Remove Auth0Debug component from production

## Auth0 Configuration Status
- ✅ Domain accessible: `dev-jwnud3v8ghqnyygr.us.auth0.com`
- ✅ Client ID configured: `KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn`
- ❌ **NEED TO FIX**: Callback URLs in Auth0 dashboard
- ✅ Frontend configuration: Properly set up
- ✅ Error handling: Enhanced with debug info 